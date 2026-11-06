% Step 2 addendum 3 §2c G1b: CoSMoMVPA on a constructed dataset whose first chunk holds one class only.
% octave --no-gui add3_cosmo_errcheck.m <cosmo_dir> <out_txt>   (writes "error: <message>" or "no error")
args = argv();
addpath(genpath(fullfile(args{1}, 'mvpa')));
ds = struct('samples', randn(80, 5));
ds.sa.targets = [ones(40, 1); repmat([1; 2], 20, 1)];
ds.sa.chunks = [ones(40, 1); 2 * ones(40, 1)];
fid = fopen(args{2}, 'w');
try
  cosmo_randomize_targets(ds, 'seed', 1);
  fprintf(fid, 'no error\n');
catch e
  fprintf(fid, 'error: %s\n', e.message);
end
fclose(fid);
