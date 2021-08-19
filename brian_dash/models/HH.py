import numpy as np
import brian2 as b2
import pandas as pd
from time import time
# import pylab as plt
from brian_dash.input_factory import *

# import matplotlib.pyplot as plt
b2.prefs.codegen.target = 'numpy'


# def plot_data(state_monitor, title=None):
#     """Plots the state_monitor variable "vm" vs. time.

#     Args:
#         state_monitor (StateMonitor): the data to plot
#         title (string, optional): plot title to display
#     """

#     fig, ax = plt.subplots(1, figsize=(10, 3))

#     ax.plot(state_monitor.t / b2.ms, state_monitor.vm[0] / b2.mV, lw=2)

#     ax.set_xlabel("t [ms]")
#     ax.set_ylabel("v [mV]")
#     plt.grid()

#     plt.axis((
#         0,
#         np.max(state_monitor.t / b2.ms),
#         -100, 50))

#     if title is not None:
#         ax.set_title(title)

#     plt.show()

def filter_dataframe(df, label):
    """
    filter dataframe

    Parameters
    -------------

    df : Dataframe
        input pandas dataframe
    label :str
        parameter name to be filtered

    return : float
        value of the filtered parameter

    """
    df0 = df.copy()

    value = df0.loc[df0['parameter'] == label]["value"].values
    if len(value > 0):
        return value[0]
    else:
        return None


def simulate_HH_neuron(par, input_current, simulation_time):
    """
    A Hodgkin-Huxley neuron implemented in Brian2.

    Args:
        input_current (TimedArray): Input current injected into the HH neuron
        simulation_time (float): Simulation time [seconds]

    Returns:
        StateMonitor: Brian2 StateMonitor with recorded fields
        ["vm", "I_e", "m", "n", "h"]
    """

    # neuron parameters
    El = filter_dataframe(par, "El") * b2.mV
    Ek = filter_dataframe(par, "Ek") * b2.mV
    Ena = filter_dataframe(par, "Ena") * b2.mV
    gl = filter_dataframe(par, "gl") * b2.msiemens
    gk = filter_dataframe(par, "gk") * b2.msiemens
    gna = filter_dataframe(par, "gna") * b2.msiemens
    C = filter_dataframe(par, "C") * b2.ufarad
    v0 = filter_dataframe(par, "v0") * b2.mV

    # forming HH model with differential equations
    eqs = """
    I_e = input_current(t,i) : amp
    membrane_Im = I_e + gna*m**3*h*(Ena-vm) + \
        gl*(El-vm) + gk*n**4*(Ek-vm) : amp
    
    alphan = 0.01/mV * (-60.0*mV - vm) / (exp((-60.0*mV - vm) / (10.0*mV)) - 1.0)/ms: Hz
    alpham = (vm + 45.0*mV) / (10.0*mV) / (1.0 - exp(-(vm + 45.0*mV) / (10.0*mV)))/ms : Hz
    alphah = 0.07*exp(-(vm + 70*mV)/(20.*mV))/ms : Hz
    
    betan = 0.125 * exp(-(vm + 70.0*mV) / (80.0*mV))/ms: Hz
    betam = 4.0 * exp(-(vm + 70.0*mV) / (18.0*mV))/ms: Hz
    betah = 1. / (exp(-(vm + 40.0*mV) / (10.0*mV)) + 1.0)/ms : Hz
    
    dn/dt = alphan*(1-n)-betan*n : 1
    dm/dt = alpham*(1-m)-betam*m : 1
    dh/dt = alphah*(1-h)-betah*h : 1
    
    dvm/dt = membrane_Im/C : volt
    """

    neuron = b2.NeuronGroup(1, eqs, method="exponential_euler")

    # parameter initialization [come from x_inf(v) {x:m,n,h}]
    neuron.vm = v0
    neuron.m = "alpham/(alpham+betam)"  # 0.05
    neuron.h = "alphah/(alphah+betah)"  # 0.60
    neuron.n = "alphan/(alphan+betan)"  # 0.32

    # tracking parameters
    state_monitor = b2.StateMonitor(
        neuron, ["vm", "I_e", "m", "n", "h"], record=True)

    # running the simulation
    hh_net = b2.Network(neuron)
    hh_net.add(state_monitor)
    hh_net.run(simulation_time)

    t = state_monitor.t / b2.ms
    v = state_monitor.vm[0] / b2.mV
    m = state_monitor.m[0]
    n = state_monitor.n[0]
    h = state_monitor.h[0]
    I = state_monitor.I_e[0]

    return {"t": t,
            "v": v,
            "m": m,
            "h": h,
            "n": n,
            "I": I}


if __name__ == "__main__":

    start = time()
    par = pd.read_csv("HH.csv")
    # current = get_step_current(0, 200, b2.ms, 7.0 * b2.uA)
    # current = get_ramp_current(0,200, b2.ms, 2.*b2.uA, 7.*b2.uA)
    current = get_sinusoidal_current(0, 200, b2.ms, 3*b2.uA, 10*b2.Hz, 2*b2.uA)
    data = state_monitor = simulate_HH_neuron(par, current, 200 * b2.ms)
    print("done in {} seconds.".format(time() - start))
    print(data['I'])
    # print(np.diff(data['t']))
    # plot_data(state_monitor, title="HH Neuron")
