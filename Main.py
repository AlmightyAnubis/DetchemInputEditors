from GeneralUtil import SelectionDialog

keys = ["Mechanism Editor","Thermal Data Comparer","Chemical Data Manager"]

mode = SelectionDialog.GeneralDialog("Select Input File Editor",
                                     keys).center().show()
if mode == "":
    exit(0)

if mode == "Mechanism Editor":
    from MechanismEditorPackage import MechanismEditor
    editor = MechanismEditor
if mode == "Thermal Data Comparer":
    from ThermalDataComparePackage import ThermalDataCompare
    editor = ThermalDataCompare
if mode == "Chemical Data Manager":
    from ChemDataManager.GUIs import SelectionGui
    editor = SelectionGui
