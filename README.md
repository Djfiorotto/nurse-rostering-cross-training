# Mathematical Formulations for Cross-Training Flexibility and Chaining in Nurse Workforce Allocation

This repository contains the dataset (problem instances) and the mathematical optimization codes to reproduce the computational experiments presented in the paper. 

The framework is implemented in Python using the **IBM ILOG CPLEX Optimization Studio** (via `docplex`) to solve mid-term nurse scheduling problems under demand uncertainty and staff flexibility policies.

## 📁 Repository Structure

```text
├── README.md               # This instruction manual
├── requirements.txt        # Required Python packages
├── src/                    # Optimization source code
│   ├── nurse_functions.py  # Mathematical models and cross-training heuristics
│   └── main_executor.py    # Parallel execution script over 100 simulation runs
└── instances/              # Processed problem instances (Excel files)
    ├── n20I1.xlsx
    ├── n20I2.xlsx
    ├── n20I3.xlsx
    ├── n30I1.xlsx
    ├── n30I2.xlsx
    ├── n30I3.xlsx
    ├── n40I1.xlsx
    ├── n40I2.xlsx
    └── n40I3.xlsx
```

## 📊 Data Instances Layout

Each file in the `instances/` directory corresponds to a specific configuration of nurses (20, 30, or 40) and clinical units (4, 5, or 6). To ensure clean replication, all deprecated worksheets have been removed, leaving exactly **5 standard sheets** per file:

* **`Area`**: Vector containing the number of dedicated nurses originally assigned to each unit.
* **`Param_values`**: Scalar parameters of the problem, including cost coefficients (\(c^0, c^R, c^+\)), bounds, horizon length (nD = 10), and day periods (nP = 24).
* **`ShiftsIn`**: Matrix specifying the operational structure of the 5 available shifts (start period, end period, and duration).
* **`Asp`**: A binary matrix mapping whether a given shift s covers a specific period p.
* **`Ejdp`**: The baseline deterministic expected demand of nurses per unit, day, and period.

## 📈 Stochastic Demand Generation & Reproducibility

As detailed in the manuscript's computational setup, **the 100 stochastic demand scenarios are generated dynamically (*on-the-fly*)** inside the script during execution. They are not stored as standalone static files.

The function `read_data3_DemandSimulation` reads the baseline expected demand (`Ejdp`) and automatically introduces a randomized additive deviation (\(\alpha_{jd}\)) sampled from a discrete uniform distribution \(U\{-2, -1, 0, 1, 2\}\) for daytime shifts. Night shifts remain deterministic. This process evaluates model robustness under realistic demand surges.

To guarantee **exact numerical replication** across different computers, random seeds are initialized in the script so that the pseudo-random sequence generates the exact same 100 sequential demand scenarios for every execution block.

## 🚀 How to Run the Experiments

### 1. Prerequisites
Make sure you have Python 3.7+ installed along with a valid license/installation of **IBM ILOG CPLEX**.

### 2. Installation
Clone this repository and install the required dependencies (including parallel processing tools) via terminal:

```bash
git clone https://github.com
cd YOUR_REPOSITORY_NAME
pip install -r requirements.txt
```

### 3. Execution
To execute the complete optimization model matrix utilizing multi-core parallel processing (via `mpi4py`), run:

```bash
python src/main_executor.py
```

The script will automatically solve the scheduling model across all cross-training policies (Standard Chain, Best Chain, and Flexibility as a Decision Variable) for 100 simulation loops per configuration. Aggregated `.csv` reports will be exported directly to a newly generated `Results/` folder.
