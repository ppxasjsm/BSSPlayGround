#!/usr/bin/env python
# coding: utf-8

# ## Conformational analysis of a small molecule
# Conformational analysis node modeled based on a workflow from Inaki, based on their protocols and input files
import BioSimSpace as BSS
import os
import subprocess

# Author and licencing
node = BSS.Gateway.Node("A node to parameterise a small molecule, run MD and do a conformational analysis.")
node.addAuthor(name="Antonia Mey", email="antonia.mey@ed.ac.uk", affiliation="University of Edinburgh")
node.setLicense("GPLv3")

# Input controls

node.addInput("file", BSS.Gateway.File(help="A molecular input file, e.g. a PDB file."))

node.addInput("forcefield", BSS.Gateway.String(help="The name of the force field to use for parameterisation.",
                                               allowed=BSS.Parameters.forceFields(), default="gaff"))

node.addInput("water", BSS.Gateway.String(help="The name of the water model to use for solvation.",
                                          allowed=BSS.Solvent.waterModels(), default="tip3p"))
node.addInput("box_size", BSS.Gateway.Length(help="The base length of the cubic simulation box.", unit="nanometer"))
node.addInput("ion_conc", BSS.Gateway.Float(help="The ionic concentration in mol/litre.",
                                            minimum=0, maximum=1, default=0))
node.addInput("minimise", BSS.Gateway.String(help="Config file for minimisation"))
node.addInput("step2", BSS.Gateway.String(help="Config file for step2 equilibration"))
node.addInput("step3", BSS.Gateway.String(help="Config file for step3 equilibration"))
node.addInput("step4", BSS.Gateway.String(help="Config file for step4 equilibration"))
node.addInput("step5", BSS.Gateway.String(help="Config file for step5 equilibration"))
node.addInput("production", BSS.Gateway.String(help="Config file for production run"))
node.addInput("cpptraj", BSS.Gateway.String(help="Config file for running cpptraj"))
node.addInput("cpptraj_exec", BSS.Gateway.String(help="Path to executable of CCPtraj"))
node.addInput("exe", BSS.Gateway.String(help="Path to MD executable"))

node.showControls()


# ## Setting the system up
# The following reads and parametrises a small molecule and will save it the specified output.
print('Setting upt the system.......')
system = BSS.IO.readMolecules(node.getInput("file"))
molecule = system.getMolecules()[0]
molecule = BSS.Parameters.parameterise(molecule, node.getInput("forcefield")).getMolecule()
system = BSS.Solvent.solvate(node.getInput("water"), molecule=molecule,
                                                     box=3 * [node.getInput("box_size")],
                                                     ion_conc=node.getInput("ion_conc"))

node.setOutput("system", BSS.IO.saveMolecules("system", system, ["prm7", "rst7", "PDB"]))
print('Done.......')

# ## Setting some information on current working directories and executables to use
cwd = os.getcwd()
exe = node.getInput("exe")


# ## Step 1-5 of the equilibrations
# ### Minimisation
print('Minimisation 1')
w_dir = os.path.join(cwd, 'minimise')
protocol = BSS.Protocol.Minimisation()
process = BSS.Process.Amber(system, protocol, name="minimise", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("minimise"))
process.setArg('-ref', 'minimise.rst7')
prc_info = process.start()
if process.isError() == False:
    print("Minimisation 1 done.....")
minimised = process.getSystem()



# ### Minimisation 2

print('Minimisation 2....')
w_dir = os.path.join(cwd, 'eq2')
protocol = BSS.Protocol.Minimisation()
process = BSS.Process.Amber(minimised, protocol, name="equ2", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("step2"))
prc_info = process.start()

if process.isError() == False:
    print("Minimisation 2 done.....")
equ2 = process.getSystem()


# ### Equilibration 3
print('Equilibration 3....')
w_dir = os.path.join(cwd, 'eq3')
protocol = BSS.Protocol.Equilibration()
process = BSS.Process.Amber(equ2, protocol, name="equ3", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("step3"))
process.setArg('-ref', 'equ3.rst7')
prc_info = process.start()
if process.isError() == False:
    print("Equilibration 3 done.....")
equ3 = process.getSystem()


# ## Equilibration 4
print('Equilibration 4....')
w_dir = os.path.join(cwd, 'eq4')
protocol = BSS.Protocol.Equilibration()
process = BSS.Process.Amber(equ3, protocol, name="equ4", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("step4"))
process.setArg('-ref', 'equ4.rst7')
prc_info = process.start()
if process.isError() == False:
    print("Equilibration 4 done.....")

equ4 = process.getSystem()

# ## Equilibration 5
print('Equilibration 5....')
w_dir = os.path.join(cwd, 'eq5')
protocol = BSS.Protocol.Equilibration()
process = BSS.Process.Amber(equ3, protocol, name="equ5", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("step5"))
prc_info = process.start()
if process.isError() == False:
    print("Equilibration 5 done.....")
equ5 = process.getSystem()

# ## Production
# Running the production MD simulation. This may take a while. 

w_dir = os.path.join(cwd, 'prod')

print('Production....this can take a while')
protocol = BSS.Protocol.Production()
process = BSS.Process.Amber(equ5, protocol, name="prod", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("production"))
prc_info = process.start()
if process.isError() == False:
    print("Production done.....")

#traj = process.getTrajectory()


# ## Conformational analysis using pytraj

# Executing cpptraj externally. This is less than ideal, but will have to do for now
print('Running CPPTRAJ analysis....')
command = node.getInput("cpptraj_exec")+ ' -i '+node.getInput("cpptraj")
subprocess.run(command, shell=True, stdout=subprocess.PIPE)





