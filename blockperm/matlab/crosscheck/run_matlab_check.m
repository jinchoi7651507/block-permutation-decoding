function run_matlab_check(d)
%RUN_MATLAB_CHECK MATLAB/Octave side of the cross-check: same features, folds and nearest-centroid decoder as
%   run_python_check.py, exact block permutation null; compares the nulls and p values with the Python output.
%   Run from this folder: run_matlab_check('DIR')

  addpath(fullfile(fileparts(mfilename('fullpath')), '..'));
  X = csvread(fullfile(d, 'features.csv'));
  tab = csvread(fullfile(d, 'labels.csv'), 1, 0);
  runs = tab(:, 2); folds = tab(:, 3);
  py = csvread(fullfile(d, 'p_python.csv'), 1, 0);   % rows imagery, fake; columns score, n_null, p
  names = {'imagery', 'fake'}; columns = [1, 4];
  for k = 1:2
    y = tab(:, columns(k));
    f = @(l) centroid_cv_score(X, l, folds);
    [score, null, p] = block_permutation_test(f, y, runs, 'Exact', true);
    null_py = csvread(fullfile(d, sprintf('null_python_%s.csv', names{k})));
    diff = max(abs(sort(null) - null_py));
    fprintf('%s: score %.4f, %d arrangements, p %.4f; Python p %.4f; max |null difference| %.3g\n', ...
            names{k}, score, numel(null), p, py(k, 3), diff);
    assert(numel(null) == py(k, 2) && abs(p - py(k, 3)) < 1e-12 && diff < 1e-9 && abs(score - py(k, 1)) < 1e-12, ...
           'MATLAB and Python disagree for %s', names{k});
  end
  fprintf('cross-check passed: same nulls and p values\n');
end


function s = centroid_cv_score(X, y, folds)
  % Mean over folds of the held-out accuracy of a nearest-centroid classifier (ties go to the lower class).
  classes = unique(y);
  acc = zeros(max(folds), 1);
  for k = 1:max(folds)
    te = folds == k; tr = ~te;
    dist = zeros(sum(te), numel(classes));
    for c = 1:numel(classes)
      mu = mean(X(tr & y == classes(c), :), 1);
      dist(:, c) = sum((X(te, :) - mu) .^ 2, 2);
    end
    [~, idx] = min(dist, [], 2);
    acc(k) = mean(classes(idx) == y(te));
  end
  s = mean(acc);
end
