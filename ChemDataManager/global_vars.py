from ChemDataManager.ChemDataFormat import ChemData
from ChemDataManager.SourceFormat import Source

# [Name, [MolData, ThermData]]
chemData: dict[str, tuple[list[ChemData],list[ChemData]]]
libData: dict[int, Source]

# [Name, [MolData, ThermData]]
selected_data: dict[str, tuple[ChemData|None,ChemData|None]]

# Name Dict for to long names
name_dict = dict[str,str]


# Config Data Storage
author = ""
university = ""
email = ""