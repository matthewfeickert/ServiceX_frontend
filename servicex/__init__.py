# Copyright (c) 2024, IRIS-HEP
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
from servicex import dataset_group
from servicex import models
from servicex import servicex_client
from servicex import dataset_identifier
from servicex.databinder_models import Sample, General, ServiceXSpec
from servicex.func_adl.func_adl_dataset import FuncADLQuery_Uproot as FuncADL_Uproot
from servicex.uproot_raw.uproot_raw import UprootRawQuery as UprootRaw
from servicex.python_dataset import PythonQuery as PythonFunction
from servicex.servicex_client import ServiceXClient, deliver
from .query_core import Query
from .models import ResultFormat, ResultDestination
from .dataset_group import DatasetGroup
from .dataset_identifier import RucioDatasetIdentifier, FileListDataset
import servicex.dataset as dataset
import servicex.query as query

__all__ = [
    "ServiceXClient",
    "Query",
    "DatasetGroup",
    "ResultFormat",
    "ResultDestination",
    "servicex_client",
    "dataset_group",
    "models",
    "dataset_identifier",
    "RucioDatasetIdentifier",
    "FileListDataset",
    "FuncADL_Uproot",
    "UprootRaw",
    "PythonFunction",
    "Sample",
    "General",
    "DefinitionList",
    "ServiceXSpec",
    "deliver",
    "dataset",
    "query"
]
