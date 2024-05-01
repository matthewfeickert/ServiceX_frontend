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
from enum import Enum
from typing import Union, Optional, Callable, List
from pydantic import model_validator, StringConstraints, ConfigDict, BaseModel, Field, validator

from servicex.dataset_identifier import RucioDatasetIdentifier, FileListDataset
from servicex.func_adl import func_adl_dataset
from typing_extensions import Annotated


class Sample(BaseModel):
    Name: str
    Codegen: Optional[str] = None
    RucioDID: Optional[str] = None
    XRootDFiles: Optional[Union[str, List[str]]] = None
    NFiles: Optional[int] = Field(default=None)
    Function: Optional[Union[str, Callable]] = Field(default=None)
    Query: Optional[Union[str, func_adl_dataset.Query]] = Field(default=None)
    Tree: Optional[str] = Field(default=None)
    IgnoreLocalCache: bool = False
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def dataset_identifier(self):
        if self.RucioDID:
            return RucioDatasetIdentifier(self.RucioDID, num_files=self.NFiles or 0)
        elif self.XRootDFiles:
            return FileListDataset(self.XRootDFiles)

    @model_validator(mode="after")
    def validate_did_xor_file(cls, values):
        """
        Ensure that only one of RootFile or RucioDID is specified.
        :param values:
        :return:
        """
        if values['XRootDFiles'] and values['RucioDID']:
            raise ValueError("Only specify one of XRootDFiles or RucioDID, not both.")
        if not values['XRootDFiles'] and not values['RucioDID']:
            raise ValueError("Must specify one of XRootDFiles or RucioDID.")
        return values

    @model_validator(mode="after")
    def validate_function_xor_query(cls, values):
        """
        Ensure that only one of Function or Query is specified.
        :param values:
        :return:
        """
        if values['Function'] and values['Query']:
            raise ValueError("Only specify one of Function or Query, not both.")
        if not values['Function'] and not values['Query']:
            raise ValueError("Must specify one of Function or Query.")
        return values


class General(BaseModel):
    class OutputFormatEnum(str, Enum):
        parquet = "parquet"
        root = "root-file"

    class DeliveryEnum(str, Enum):
        LocalCache = "LocalCache"
        SignedURLs = "SignedURLs"

    ServiceX: str = Field(..., alias="ServiceX")
    Codegen: str
    OutputFormat: Union[OutputFormatEnum,
        Annotated[str, StringConstraints(pattern='^(parquet|root-file)$')]] = Field(default=OutputFormatEnum.root)  # NOQA F722

    Delivery: Union[DeliveryEnum, Annotated[str, StringConstraints(pattern='^(LocalCache|SignedURLs)$')]] = Field(default=DeliveryEnum.LocalCache) # NOQA F722


class Definition(BaseModel):
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def check_def_name(cls, values):
        """
        Ensure that the definition name is DEF_XXX format
        :param values:
        :return:
        """
        for field in values:
            if not field.startswith("DEF_"):
                raise ValueError(f"Definition key {field} does not meet the convention of DEF_XXX format") # NOQA E501
        return values


class ServiceXSpec(BaseModel):
    General: General
    Sample: List[Sample]
    Definition: Optional[Definition] = None

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator('Sample')
    def check_tree_property(cls, v, values):
        if 'General' in values and values['General'].Codegen != 'uproot':
            for sample in v:
                if 'Tree' in sample:
                    raise ValueError('"Tree" property is not allowed when codegen is not "uproot"')
        return v

    @model_validator(mode="before")
    @classmethod
    def replace_definition(cls, values):
        """
        Replace the definition name with the actual definition value looking
        through the Samples and the General sections
        :param values:
        :return:
        """
        def replace_value_from_def(value, defs):
            """
            Replace the value with the actual definition value
            :param value:
            :param defs:
            :return:
            """
            if isinstance(value, dict):
                for field in value.keys():
                    value[field] = replace_value_from_def(value[field], defs)
            elif isinstance(value, str):
                if value.startswith("DEF_"):
                    if value in defs:
                        value = defs[value]
                    else:
                        raise ValueError(f"Definition {value} not found")
            return value

        if 'Definition' in values and values['Definition'] is not None:
            defs = values['Definition'].dict()
        else:
            defs = {}

        for sample_field in values['Sample']:
            replace_value_from_def(sample_field.__dict__, defs)

        replace_value_from_def(values['General'].__dict__, defs)

        return values
