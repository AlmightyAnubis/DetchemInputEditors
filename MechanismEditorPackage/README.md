# Mechanism Editor
The Mechanism Editor is a tool to modify mechanisms and make them thermodynamic consistent using the **ADJUST** tool.
## How it works
When opening the editor, a window opens in which the mechanism that should be edited needs to be selected. 
Furthermore, a file for the thermodynamic data of the species needs to be provided. It has to be called ***thermdata*** 
or ***thermdata.txt***, otherwise the program will crash.
The first time you open a mechanism, the program will create a file called ***adjust.json*** and stop directly.
In this file, you can set the temperature range, in which it **ADJUST** should work. Furthermore, you can define 
surface species. 