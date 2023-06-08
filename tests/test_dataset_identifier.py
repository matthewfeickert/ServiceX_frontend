# Copyright (c) 2022, IRIS-HEP
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
from servicex_client.dataset_identifier import DataSetIdentifier, RucioDatasetIdentifier, \
    FileListDataset


def test_did():
    did = DataSetIdentifier(scheme="rucio", dataset="123-455")
    assert did.did == "rucio://123-455"


def test_rucio():
    did = RucioDatasetIdentifier("123-456")
    assert did.did == "rucio://123-456"


def test_file_list():
    did = FileListDataset(["c:/foo.bar"])
    assert did.files == ["c:/foo.bar"]


def test_single_file():
    did = FileListDataset("c:/foo.bar")
    assert did.files == ["c:/foo.bar"]


def test_populate_transform_request(transform_request):
    did = FileListDataset(["c:/foo.bar"])
    did.populate_transform_request(transform_request)
    assert transform_request.file_list == ["c:/foo.bar"]

    did2 = RucioDatasetIdentifier("123-456")
    did2.populate_transform_request(transform_request)
    assert transform_request.did == "rucio://123-456"