import copy

from TestArea.ReadFile import read_moldata, write_moldata

gri_data = read_moldata("gri_30.txt",1)
SANDIA  = read_moldata("SAND86-8246.txt",2)
copyElements =  {key: value for key, value in SANDIA.items() if "=>" in value.comment_chem}
print("Copy Elements in SANDIA(",len(copyElements),"): ",copyElements.keys())
SANDIA = {key: value for key, value in SANDIA.items() if "=>" not in value.comment_chem}

gri_key = set(gri_data.keys())
sandia_key = set(SANDIA.keys())

both = gri_key.intersection(sandia_key)
additional_in_gri_key = [x for x in gri_key if x not in sandia_key]
additional_in_sandia_key = [x for x in sandia_key if x not in gri_key]


for key,value in gri_data.items():
    old_comment = value.comment_chem
    value.comment_chem = " ! GRI_MECH"
    if old_comment != "":
        if old_comment[0] == "!":
            old_comment = old_comment[1:]
            old_comment = old_comment.strip()
            value.comment_chem = value.comment_chem + "(" + old_comment + ")"

for key,value in SANDIA.items():
    old_comment = value.comment_chem
    value.comment_chem = " ! SANDIA"
    if old_comment != "":
        if old_comment[0] == "!":
            old_comment = old_comment[1:]
            old_comment = old_comment.strip()
            value.comment_chem = value.comment_chem + "(" + old_comment + ")"


combined = copy.deepcopy(SANDIA)
combined.update(gri_data)

print("In Both: ",len(both),both)

counter = 0
for key in both:
    value_gri = gri_data[key]
    value_SANDIA = SANDIA[key]
    if value_gri.species != value_SANDIA.species:
        print("Diff species for: ", key)
        counter += 1
    elif value_gri.geometry != value_SANDIA.geometry:
        print("Diff geometry for: ", key)
        counter += 1
    elif value_gri.lennard_jones_potential != value_SANDIA.lennard_jones_potential:
        print("Diff lennard jones potential for: ", key)
        counter += 1
    elif value_gri.lennard_jones_collision != value_SANDIA.lennard_jones_collision:
        print("Diff lennard jones collision for: ", key)
        counter += 1
    elif value_gri.dipole_moment != value_SANDIA.dipole_moment:
        print("Diff dipole moment for: ", key)
        counter += 1
    elif value_gri.polarizability != value_SANDIA.polarizability:
        print("Diff polarizability for: ", key)
        counter += 1
    elif value_gri.rotational_relaxation_collision_number != value_SANDIA.rotational_relaxation_collision_number:
        print("Diff rotational relaxation collision number for: ", key)
        counter += 1
    else:
        continue



print(counter)
print("In Additional in Gri: ",additional_in_gri_key)
print("In Additional in Sandia: ",additional_in_sandia_key)

combined = dict(sorted(combined.items()))
write_moldata("combined.txt",combined)




