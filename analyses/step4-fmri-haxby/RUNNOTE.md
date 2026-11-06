# Steps 4 and 5 run note

- 2026-11-02 18:50 KST: design v2 hash lists committed (3f3e25a) and submitted to the OpenTimestamps calendars (proofs committed 06c32ba, pending). No data of either step downloaded or opened.
- Orchestration: `code/chain_45.sh` (written after the stamp, committed before any data) only waits for both Bitcoin attestations, checks both hash lists, and then runs the timestamped scripts in the order of DESIGN §11 (step 4) and §10 (step 5) with the documented arguments; it contains no analysis choice. It is not under the timestamp. Data folders: `<home>/Downloads/step45-data/haxby` and `.../pamap2` (outside the repository). Python: the quick-path environment with nibabel 5.3.2 (versions asserted by the runners).
- (A note on an unrelated file of the working repository, restored from version control before this commit, is omitted in this copy.)
