# Copyright (c) 2019-2020, IRIS-HEP
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import Any, AsyncIterator, Optional, cast, Dict
import logging

import backoff
from backoff import on_exception
from confuse import ConfigView
from minio import Minio, ResponseError

from .utils import ServiceXException


class MinioAdaptor:
    # Threadpool on which downloads occur. This is because the current minio library
    # uses blocking http requests, so we can't use asyncio to interleave them.
    _download_executor = ThreadPoolExecutor(max_workers=5)

    def __init__(self, mino_endpoint: str,
                 access_key: str = 'miniouser',
                 secretkey: str = 'leftfoot1'):
        self._endpoint = mino_endpoint
        self._access_key = access_key
        self._secretkey = secretkey

        self._client = Minio(self._endpoint,
                             access_key=self._access_key,
                             secret_key=self._secretkey,
                             secure=False)

    @on_exception(backoff.constant, ResponseError, interval=0.1)
    def get_files(self, request_id):
        return [f.object_name for f in self._client.list_objects(request_id)]

    async def download_file(self,
                            request_id: str,
                            bucket_fname: str,
                            output_file: Path) -> None:
        '''
        Download a single file to a local temp file.

        Arguments:
            minio_client        Open and authenticated minio client
            request_id          The id of the request we are going after
            bucket_fname        The fname of the bucket
            output_file         Filename where we should write this file.

        Notes:
            - Download to a temp file that is renamed at the end so that a partially
              downloaded file is not mistaken as a full one
            - Run with async, despite minio not being async.
        '''
        # Make sure the output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # We are going to build a temp file, and download it from there.
        def do_copy() -> None:
            temp_file = output_file.parent / f'{output_file.name}.temp'
            try:
                self._client.fget_object(request_id, bucket_fname, str(temp_file))
                temp_file.rename(output_file)
            except Exception as e:
                raise ServiceXException(
                    f'Failed to copy minio bucket {bucket_fname} from request '
                    f'{request_id} to {output_file}') from e

        # If the file exists, we don't need to do anything.
        if output_file.exists():
            return

        # Do the copy, which might take a while, on a separate thread.
        return await asyncio.wrap_future(self._download_executor.submit(do_copy))


class MinioAdaptorFactory:
    '''A factor that will return, when asked, the proper minio adaptor to use for a request
    to get files from ServiceX.
    '''
    def __init__(self, c: Optional[ConfigView] = None,
                 always_return: Optional[MinioAdaptor] = None):
        '''Create the factor with a possible adaptor to always use

        Args:
            always_return (Optional[MinioAdaptor], optional): The adaptor to always use. If none,
            then one will be created by the best other available method. Defaults to None.
        '''
        # Get the defaults setup.
        self._always = always_return
        self._config_adaptor = None
        if self._always is None and c is not None:
            self._config_adaptor = self._from_config(c)

    def from_best(self, transation_info: Optional[Dict[str, str]] = None) -> MinioAdaptor:
        '''Using the information we have, create the proper Minio Adaptor with the correct
        endpoint and login information. Order of adaptor generation:

        1. The `always_return` option from the ctor
        1. Use info from the `translation_info`
        1. Use the info from the config handed in to the ctor

        Raises:
            Exception: If we do not have enough information to create an adaptor, this is raised.

        Returns:
            MinioAdaptor: The adaptor that can be used to extract the data from minio for this
            request.
        '''
        if self._always is not None:
            logging.getLogger(__name__).debug('Using the pre-defined minio_adaptor')
            return self._always
        if transation_info is not None:
            if 'minio-endpoint' in transation_info \
                    and 'minio-access-key' in transation_info \
                    and 'minio-secret-key' in transation_info:
                logging.getLogger(__name__).debug('Using the request-specific minio_adaptor')
                return MinioAdaptor(transation_info['minio-endpoint'],
                                    transation_info['minio-access-key'],
                                    transation_info['minio-secret-key'])
        if self._config_adaptor is not None:
            logging.getLogger(__name__).debug('Using the config-file minio_adaptor')
            return self._config_adaptor
        raise Exception("Do not know how to create a Minio Login info")

    def _from_config(self, c: ConfigView) -> MinioAdaptor:
        '''Extract the Minio config information from the config file(s). This will be used
        if minio login information isn't returned from the request.

        Args:
            c (ConfigView): The loaded config

        Returns:
            MinioAdaptor: The adaptor that uses the config's login information.
        '''
        c_api = c['api_endpoint']
        end_point = cast(str, c_api['minio_endpoint'].as_str_expanded())

        # Grab the username and password if they are explicitly listed.
        if 'minio_username' in c_api:
            username = c_api['minio_username'].as_str_expanded()
            password = c_api['minio_password'].as_str_expanded()
        elif 'username' in c_api:
            username = c_api['username'].as_str_expanded()
            password = c_api['password'].as_str_expanded()
        else:
            username = c_api['default_minio_username'].as_str_expanded()
            password = c_api['default_minio_password'].as_str_expanded()

        return MinioAdaptor(end_point,
                            access_key=cast(str, username),
                            secretkey=cast(str, password))


async def find_new_bucket_files(adaptor: MinioAdaptor,
                                request_id: str,
                                update: AsyncIterator[Any]) -> AsyncIterator[str]:
    '''
    Each time we get something from the async iterator, check to see if
    there are any files present.
    '''
    seen = []
    async for _ in update:
        # Sadly, this is blocking, and so may hold things up
        files = adaptor.get_files(request_id)

        # If there are new files, pass them on
        for f in files:
            if f not in seen:
                seen.append(f)
                yield f
