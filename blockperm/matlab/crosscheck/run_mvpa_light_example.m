function run_mvpa_light_example(d, mvpa_light_dir)
%RUN_MVPA_LIGHT_EXAMPLE The README's MVPA-Light call on the cross-check EEG features (Octave needs the packages
%   statistics and datatypes). run_mvpa_light_example('DIR', 'path/to/MVPA-Light')

  if exist('OCTAVE_VERSION', 'builtin')
    pkg load statistics
  end
  addpath(fullfile(fileparts(mfilename('fullpath')), '..'));
  addpath(genpath(mvpa_light_dir));
  X = csvread(fullfile(d, 'features.csv'));
  tab = csvread(fullfile(d, 'labels.csv'), 1, 0);
  clabel = tab(:, 1) + 1; run = tab(:, 2); folds = tab(:, 3);
  cfg = struct('classifier', 'lda', 'metric', 'accuracy', 'cv', 'predefined', 'fold', folds, 'feedback', 0);
  score_fcn = @(labels) mv_classify(cfg, X, labels);
  first = score_fcn(clabel);
  repeat = score_fcn(clabel);
  assert(first == repeat, 'the score must not change between calls with the same labels');
  [score, null, p] = block_permutation_test(score_fcn, clabel, run, 'NPermutations', 49, 'Seed', 0);
  fprintf('MVPA-Light: score %.4f (repeated call %.4f), %d permutations, p %.3f\n', score, repeat, numel(null), p);
end
