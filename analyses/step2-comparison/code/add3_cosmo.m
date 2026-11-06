% Step 2 addendum 3 §2b/§2c: CoSMoMVPA building blocks in the documented permutation loop, on the replicate files of
% add3_tools_data.py (CoSMoMVPA ships no single-subject permutation function; FAQ: "through cosmo_randomize_targets
% and a for-loop the user can do that themselves"; examples/run_permutation_test.m).
% octave --no-gui add3_cosmo.m <cosmo_dir> <data_dir> <out_csv> <worker> <of> <n_perm> <gate_dir or "-"> <variant>
%   variant main   : leave-one-chunk-out (cosmo_nfold_partitioner) balanced by cosmo_balance_partitions (defaults:
%                    one repeat, balanced test sets, seed 1), cosmo_crossvalidation_measure with cosmo_classify_lda
%                    (regularisation 0.01), accuracy. The measure refuses unbalanced partitions; the error text's
%                    scenario (1) "the input is an MEEG dataset ... You probably want to use cosmo_balance_partitions"
%                    is followed. Balancing is applied to the observed and to every permuted dataset (the balanced
%                    subsets are index sets; the FAQ's own loop recomputes the partitions per null dataset).
%           zscore : as main after z-scoring every feature within each chunk (a feature constant in a chunk -> 0).
%           unbal  : no balancing; cosmo_crossvalidation_measure with 'check_partitions' false (the remedy the
%                    measure forwards; the error text's scenario (4) names the equivalent unbalanced_partitions_ok).
% Null: n_perm draws of cosmo_randomize_targets(ds, 'seed', 1000*rep + i) (labels permuted within each chunk;
% error if a chunk lacks a target), whole cross-validation rerun; p = (1 + #{null >= obs}) / (n_perm + 1).
% CSV line: layout, rep, variant, p, observed accuracy, error flag, n_perm, seconds, error message (commas removed).
% Gate (§2c G1, variant main only): for L2 replicates 0-49 the permutation index vectors -> <gate_dir>/L2_rXXX_perm.mat.
% Resumable by (layout, rep, variant).
1;
function part = make_partitions(ds, variant)
  part = cosmo_nfold_partitioner(ds);
  if ~strcmp(variant, 'unbal'), part = cosmo_balance_partitions(part, ds); end
end

args = argv();
cosmo_dir = args{1}; data_dir = args{2}; out_csv = args{3};
worker = str2double(args{4}); of = str2double(args{5}); n_perm = str2double(args{6}); gate_dir = args{7};
variant = args{8};
addpath(genpath(fullfile(cosmo_dir, 'mvpa')));
done = {};
if exist(out_csv, 'file')
  fid = fopen(out_csv, 'r'); l = fgetl(fid);
  while ischar(l)
    f = strsplit(l, ','); done{end+1} = [f{1} '_' f{2} '_' f{3}]; l = fgetl(fid);
  end
  fclose(fid);
end
files = dir(fullfile(data_dir, 'L*_r*.mat'));
names = sort({files.name});
for k = 1:numel(names)
  if mod(k - 1, of) ~= worker, continue; end
  tok = regexp(names{k}, 'L(\d)_r(\d+)\.mat', 'tokens'){1};
  j = str2double(tok{1}); rep = str2double(tok{2});
  if any(strcmp(done, sprintf('%d_%d_%s', j, rep, variant))), continue; end
  m = load(fullfile(data_dir, names{k}));                 % outside the error capture: a bad file stops the worker
  ds = struct('samples', m.X);
  ds.sa.targets = m.targets(:); ds.sa.chunks = m.chunks(:);
  ds.fa.i = 1:size(m.X, 2);
  ds.a.fdim.labels = {'i'}; ds.a.fdim.values = {1:size(m.X, 2)};
  if strcmp(variant, 'zscore')
    for c = unique(ds.sa.chunks)'
      r = ds.sa.chunks == c; x = ds.samples(r, :);
      s = std(x, 0, 1); s(s == 0) = 1;
      ds.samples(r, :) = (x - mean(x, 1)) ./ s;
    end
  end
  margs = struct('classifier', @cosmo_classify_lda, 'output', 'accuracy');
  if strcmp(variant, 'unbal'), margs.check_partitions = false; end
  t0 = tic; err = 0; p = NaN; obs = NaN; msg = '';
  try
    margs.partitions = make_partitions(ds, variant);
    r = cosmo_crossvalidation_measure(ds, margs); obs = r.samples;
    null = zeros(n_perm, 1);
    keep_perm = strcmp(variant, 'main') && (~strcmp(gate_dir, '-')) && j == 2 && rep < 50;
    if keep_perm, perms = zeros(numel(ds.sa.targets), n_perm); end
    for i = 1:n_perm
      [t, perm] = cosmo_randomize_targets(ds, 'seed', 1000 * rep + i);
      if keep_perm, perms(:, i) = perm(:); end
      d2 = ds; d2.sa.targets = t(:);
      m2 = margs; m2.partitions = make_partitions(d2, variant);
      r2 = cosmo_crossvalidation_measure(d2, m2); null(i) = r2.samples;
    end
    p = (1 + sum(null >= obs - 1e-12)) / (n_perm + 1);
    if keep_perm, save('-mat7-binary', fullfile(gate_dir, sprintf('L2_r%03d_perm.mat', rep)), 'perms'); end
  catch e
    err = 1; msg = regexprep(e.message, '[,\n\r]', ' ');
    msg = msg(1:min(end, 160));
  end
  fid = fopen(out_csv, 'a');
  fprintf(fid, '%d,%d,%s,%.10g,%.10g,%d,%d,%.1f,%s\n', j, rep, variant, p, obs, err, n_perm, toc(t0), msg);
  fclose(fid);
end
