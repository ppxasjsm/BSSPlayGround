#!/usr/bin/env python
# coding: utf-8

# ## Conformational analysis of a small molecule
# Conformational analysis node modeled based on a workflow from Inaki, based on their protocols and input files

# In[1]:


import BioSimSpace as BSS


# In[2]:


node = BSS.Gateway.Node("A node to parameterise a small molecule, run MD and do a conformational analysis.")


# In[3]:


node.addAuthor(name="Antonia Mey", email="antonia.mey@ed.ac.uk", affiliation="University of Edinburgh")
node.setLicense("GPLv3")


# In[4]:


# Below all input controls are defined, for setting up the system and running each step


# In[5]:


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


# ## Add optional output

# In[6]:


node.addOutput("system", BSS.Gateway.FileSet(help="The parameterised and solvated molecular system in AMBER format."))


# In[7]:


node.addOutput("equ5_out", BSS.Gateway.File(help="The output for equilibration 5 output."))


# In[8]:


node.showControls()


# ## Setting the system up
# The following reads and parametrises a small molecule and will save it the specified output. 

# In[9]:


system = BSS.IO.readMolecules(node.getInput("file"))
molecule = system.getMolecules()[0]
molecule = BSS.Parameters.parameterise(molecule, node.getInput("forcefield")).getMolecule()
system = BSS.Solvent.solvate(node.getInput("water"), molecule=molecule,
                                                     box=3 * [node.getInput("box_size")],
                                                     ion_conc=node.getInput("ion_conc"))

node.setOutput("system", BSS.IO.saveMolecules("system", system, ["prm7", "rst7", "PDB"]))


# ## Setting some information on current working directories and executables to use

# In[26]:


import os
cwd = os.getcwd()
exe = node.getInput("exe")


# ## Step 1-5 of the equilibrations

# ### Minimisation

# In[16]:


w_dir = os.path.join(cwd,'minimise')


# In[22]:


protocol = BSS.Protocol.Minimisation()
process = BSS.Process.Amber(system, protocol, name="minimise", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("minimise"))
process.setArg('-ref', 'minimise.rst7')


# In[23]:


prc_info = process.start()


# In[29]:


minimised = process.getSystem()


# ### Minimisation 2

# In[33]:


w_dir = os.path.join(cwd,'eq2')


# In[34]:


protocol = BSS.Protocol.Minimisation()
process = BSS.Process.Amber(minimised, protocol, name="equ2", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("step2"))


# In[35]:


prc_info = process.start()


# In[38]:


equ2 = process.getSystem()


# ### Equilibration 3

# In[39]:


w_dir = os.path.join(cwd,'eq3')


# In[40]:


protocol = BSS.Protocol.Equilibration()
process = BSS.Process.Amber(equ2, protocol, name="equ3", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("step3"))


# In[41]:


process.setArg('-ref', 'equ3.rst7')


# In[42]:


prc_info = process.start()


# In[44]:


equ3 = process.getSystem()


# ## Equilibration 4

# In[46]:


w_dir = os.path.join(cwd,'eq4')


# In[47]:


protocol = BSS.Protocol.Equilibration()
process = BSS.Process.Amber(equ3, protocol, name="equ4", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("step4"))


# In[48]:


process.setArg('-ref', 'equ4.rst7')


# In[49]:


prc_info = process.start()


# In[50]:


equ4 = process.getSystem()


# ## Equilibration 5

# In[52]:


w_dir = os.path.join(cwd,'eq5')


# In[53]:


protocol = BSS.Protocol.Equilibration()
process = BSS.Process.Amber(equ3, protocol, name="equ5", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("step5"))


# In[54]:


prc_info = process.start()


# In[60]:


equ5 = process.getSystem()


# In[64]:


process.isRunning()


# ## Production
# Running the production MD simulation. This may take a while. 

# In[65]:


w_dir = os.path.join(cwd,'prod')


# In[66]:


protocol = BSS.Protocol.Production()
process = BSS.Process.Amber(equ5, protocol, name="prod", work_dir=w_dir, exe=exe)
process.setConfig(node.getInput("production"))


# In[68]:


prc_info = process.start()


# In[74]:


process.isRunning()


# In[ ]:


traj = process.getTrajectory()


# ## Conformational analysis using pytraj

# In[80]:


#Executing cpptraj externally. This is less than ideal, but will have to do for now
import subprocess


# In[77]:


cpptraj_exec = '/home/ppxasjsm/Software/amber18/bin/cpptraj'


# In[85]:


command = node.getInput("cpptraj_exec")+ ' -i '+node.getInput("cpptraj")
#command =cpptraj_exec+ ' -i '+node.getInput("ccptraj")
subprocess.run(command, shell=True, stdout=subprocess.PIPE)


# In[ ]:




