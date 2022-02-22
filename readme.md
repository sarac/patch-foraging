# Patch-Foraging Task Code

Please cite the accompanying paper: Constantino, S.M., Daw, N.D. Learning the opportunity cost of time in a patch-foraging task. Cogn Affect Behav Neurosci 15, 837–853 (2015). https://doi.org/10.3758/s13415-015-0350-y

Hello! This repository contains the patch-foraging task code from "Learning the opportunity cost of time in a patch-foraging task".

1) Download the project 

```shell
git clone https://github.com/sarac/patch-foraging.git
```

2) Create and activate the environment with dependencies. We will use conda here:

```shell
conda env create -f environment.yml
conda activate expcode
```

3) Create a data folder to save the data and run the experiment

```shell
mkdir ../data 
cd treeExp
python main.py -w -d -i -c mad
```

For questions/comments, please contact Sara Constantino at sara.constantino@gmail.com.
