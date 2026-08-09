# Instructions for collecting and curating research data using this repo

This is an initial instruction outline which will be used to set up the pipe line using an LLM.

> [!NOTE]
> **Implemented as of 0.10.0** in `sync_from_della.sh`, `catalog.sh`, `analyze_new.sh`
> and `run_pipeline.sh` (see the "research-data pipeline" section of `README.md`),
> with two deliberate deviations from the outline below:
>
> 1. **Step 2.2 (sorting into `STATIC` / `DYNAMIC_GROWTH/SCHEMEn/`) was dropped.**
>    Nothing is moved: the local directory stays a verbatim mirror of della, so a
>    re-sync never re-downloads a run that cataloging had relocated. The naming
>    conventions already distinguish the datasets, and the driving scheme is recorded
>    in each run's `run_catalog.md` regardless.
> 2. **The folder-name vs `out.csv` check is advisory, not a gate.** Run folders use
>    several encodings and some drop the decimal point (`K0001` = 0.001,
>    `JHOM_285` = -2.85), so a strict parser would produce mostly false positives. The
>    `out.csv` header is treated as ground truth; name mismatches are reported in a
>    clearly-labelled advisory section of `run_catalog.md`. The *hard* consistency
>    check is that the parameters agree across the mu folders of one run, which does
>    land in `flagged_warning.md`.

## Keeping the data synched between the cluster computer and the local copy

The data is getting generated on the `della` cluster. Claude has access to this cluster using the della skill. The first step is to keep a directory in sync with the results on the cluster computer. 
1. Creating a simple bash script that looks like the following:

```bash
# keep data in sync
DELLA_DIR="PATH_TO_SYNC_FROM"
LOCAL_DIR="PATH_TO_SYNC_TO"

# the following is pseudo code and needs to be implemented directly
rsync dry run #check for new data
if: new_data and no_errors
	 copy to local dir
else:
	report error
```

2. Cataloging the new data

With the tools from this repo it is possible to extract the parameter runs from the folder name and check if that is consistent with the parameters reported in the `out.csv file`.

2.1 Creating a bash script that checks the following: for newly synced data check that the parameters between folder name and out.csv files are consistent. A simple text file is written to the data directory reporting all the parameters in a human-readable format (md file), including time stamp of the current cataloging. If a slurm file is available, the slurm file can be checked for errors. If errors are present, a human readable .md file should be created in the folder (`flagged_warning.md`). Using the bash tools available in the `CLAUDE.md` file the used nesspy version for that data set should be written to the folder as `{nesspy_version}.version` (the file name is the version number).

2.2 The local folder will be structures as follows:

LOCAL_DIR
---STATIC
------..
---DYNAMIC_GROWTH
-----SCHEME1
-------individual_data_folder_1
-----SCHEME2
-----SCHEME3
-----SCHEME4
-----SCHEME5
-----SCHEME6
-----OTHER

After the correct cataloging the bash script should move to the corresponding folder. The scheme was read from the files above. 

3. Running the order-disorder analysis
3.1 for all new data the full analysis suite needs to be run. No comparison between runs is needed since the relevant data is written to csv files by the analysis script. 
3.2 Check that every new run is fully analyzed including the more time consuming lattice plots.


