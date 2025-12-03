import math

import numpy as np
from matplotlib import pyplot as plt
from scipy.constants import R

from BalanceCalculator import ThermalDataReader


def pressureCorrection(pressure,temperature):
    return  R*temperature*math.log(pressure/1e5)


print(R)
data = ThermalDataReader.read_thermdata_file("berkeley_thermdata_+pd.txt")
palladium = data["PD"]
oxygen = data["O2"]


plt.close('all')
# A = A' * exp(S/R)
S = -3e2
H = -1e5
order = 0


Pd_coef = np.array(palladium.get_coefficients())
O2_coef = np.array(oxygen.get_coefficients())
print(palladium.get_temp_max())
print(palladium.get_temp_min())
print(palladium.get_temp_switch())
print(oxygen.get_temp_max())
print(oxygen.get_temp_min())
print(oxygen.get_temp_switch())




def PdO_g(T):
    g_palladium = palladium.get_g(T)
    g_oxygen = 0.5 * oxygen.get_g(T)
    bonus = -1e4 + 0.5 * (-150 + 30)*T
    #bonus = -0.2e5 - 0.1e3 * T + 0.15e0*T*T
    #return g_palladium + g_oxygen + bonus
    return -16e4-1.5e1*T





# Langmuir-Hinshelwood Assumption
def calcBalance(T, p_O2):
    #k_fwd = A_fwd * math.exp(E_a/(R*T))
    #k_bwd = A_bwd * math.exp((E_a + G)/(R*T))
    g_palladium = palladium.get_g(T)
    g_oxygen = oxygen.get_g(T)
    pressureFactor = pressureCorrection(p_O2, T)

    deltaG =PdO_g(T) - (g_palladium + 1/2 * (g_oxygen + pressureFactor))
    #print(deltaG)
    exponent = min(-deltaG/(R*T),500)
    k_A = math.exp(exponent)
    cover = k_A * p_O2**order/(1 + k_A*p_O2**order)
    return math.copysign(1,-deltaG/(R*T))
# subplot_kw={"projection": "3d"}
fig, ax = plt.subplots()

# Make the data
T = np.arange(300, 1200, 5)
p = np.arange(-5, 0.1, 0.2)
vec_funct = np.vectorize(lambda a: math.pow(10,a))
p = vec_funct(p)
p_pascal = p * 133.322368
X, Y = np.meshgrid(p_pascal, T)
Z = np.array([calcBalance(y, x) for (x, y) in zip(X.ravel(), Y.ravel())]).reshape(X.shape)
#X, Y = np.meshgrid(p, T)
X, Y = np.meshgrid(p, T)

# Default behavior is axlim_clip=False
#ax.contourf(X, Y, Z)
cf0 = ax.contourf(X, Y, Z, np.arange(0, 1, .05),
                   extend='both')
cf0 = ax.contourf(X, Y, Z,
                   extend='both')
cbar0 = plt.colorbar(cf0,)

# When axlim_clip=True, note that when a line segment has one vertex outside
# the view limits, the entire line is hidden. The same is true for 3D patches
# if one of their vertices is outside the limits (not shown).
#ax.plot_wireframe(X, Y, Z, color='C1', axlim_clip=True)

# In this example, data where x < 0 or z > 0.5 is clipped
ax.set(ylim=(450, 900))
ax.legend(['axlim_clip=False (default)', 'axlim_clip=True'])
ax.set_xscale('log')
plt.grid(True)
plt.show()

#exit()

fig, ax = plt.subplots()

# Make the data
T = np.arange(300, 1000, 5)
g_palladium = np.array([palladium.get_g(x) for x in T])
g_oxygen = np.array([0.5*oxygen.get_g(x) for x in T])
print(math.pow(10,-5)* 133.322368/1e5)
print(pressureCorrection(math.pow(10,-5)* 133.322368, 1))
pressureFactor = np.array([pressureCorrection(math.pow(10,-5)* 133.322368, x) for x in T])
g_oxygen += 0.5 * pressureFactor
g_educts = g_palladium + g_oxygen
g_palladium_ox = np.array([PdO_g(x) for x in T])
plt.plot(T, g_palladium, label='g_palladium')
plt.plot(T, g_oxygen, label='g_oxygen')
plt.plot(T, g_educts, label='g_educts')
plt.plot(T, g_palladium_ox, label='g_palladium_ox')
plt.legend()
plt.show()