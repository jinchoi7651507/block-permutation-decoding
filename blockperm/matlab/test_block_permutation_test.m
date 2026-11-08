function test_block_permutation_test()
%TEST_BLOCK_PERMUTATION_TEST Checks of block_permutation_test (MATLAB R2016b or later, or Octave 7 or later).
%   Run from this folder: test_block_permutation_test

  check_errors();
  check_counts_and_exact_p();
  check_strata();
  check_sampled_p_and_seed();
  check_draw();
  check_cell_labels();
  check_size_under_no_information();
  fprintf('all checks passed\n');
end


function check_errors()
  y = [1 1 2 2]';
  assert(raises(@() block_permutation_test(@(l) 0, [1 2 2 2]', [1 1 2 2]'), 'blockperm:notConstant'), 'label not constant');
  assert(raises(@() block_permutation_test(@(l) 0, y, [1 1 2]'), 'blockperm:length'), 'length mismatch');
  assert(raises(@() block_permutation_test(@(l) 0, y, [1 1 2 2]', 'NPermutations', 0), 'blockperm:options'), 'NPermutations < 1');
  assert(raises(@() block_permutation_test(@(l) 0, y, [1 1 2 2]', 'Exact', 'yes'), 'blockperm:options'), 'bad Exact');
  assert(raises(@() block_permutation_test(@(l) 0, y, [1 1 2 2]', 'Nperm', 10), 'blockperm:options'), 'unknown option');
end


function check_counts_and_exact_p()
  % 4 blocks, 2 per class: 6 arrangements. A score that is 1 only for the observed arrangement gives p = 1/6.
  blocks = repelem((1:4)', 3);
  y = repelem([1 2 1 2]', 3);
  f = @(l) double(isequal(l, y));
  state = warning('error', 'blockperm:fewArrangements');   % raise this warning as an error here
  warned = raises(@() block_permutation_test(f, y, blocks), 'blockperm:fewArrangements');
  warning(state);
  assert(warned, 'warning when there are fewer than 20 arrangements');
  [score, null, p] = block_permutation_test(f, y, blocks);
  assert(score == 1 && numel(null) == 6 && sum(null == 1) == 1, 'exact null has one score per arrangement');
  assert(abs(p - 1 / 6) < 1e-12, 'exact p for a unique best arrangement');
  % a score that ignores the class names (swap-symmetric) gives p = 2/6
  g = @(l) double(isequal(l, y) || isequal(3 - l, y));
  [~, ~, p2] = block_permutation_test(g, y, blocks);
  assert(abs(p2 - 2 / 6) < 1e-12, 'class swap doubles the smallest p');
end


function check_strata()
  % two strata of 4 blocks each (2 per class): 6 * 6 = 36 arrangements, all keep 2 per class per stratum
  blocks = repelem((1:8)', 2);
  y = repelem([1 2 1 2 2 1 1 2]', 2);
  strata = repelem([1 1 1 1 2 2 2 2]', 2);
  [~, null, ~] = block_permutation_test(@(l) strata_code(l), y, blocks, 'Strata', strata);
  assert(numel(null) == 36, 'strata: 36 arrangements');
  assert(numel(unique(null)) == 36, 'strata: the 36 arrangements are distinct');
end


function c = strata_code(l)
  % Number that identifies the arrangement; checks that each stratum keeps 2 blocks per class.
  b = l(1:2:end);
  assert(sum(b(1:4) == 1) == 2 && sum(b(5:8) == 1) == 2, 'strata: class counts kept within strata');
  c = sum((b(:)' - 1) .* 2 .^ (0:7));
end


function check_sampled_p_and_seed()
  % 20 blocks, 10 per class: C(20,10) = 184,756 arrangements > NPermutations, so sampling is used.
  blocks = repelem((1:20)', 2);
  y = repelem(repmat([1 2]', 10, 1), 2);
  f = @(l) mean(l(1:2:end) == 1);
  [score, n1, p1] = block_permutation_test(f, y, blocks, 'NPermutations', 99, 'Seed', 3);
  [~, n2, p2] = block_permutation_test(f, y, blocks, 'NPermutations', 99, 'Seed', 3);
  assert(numel(n1) == 99 && isequal(n1, n2) && p1 == p2, 'same seed, same null');
  expected = (1 + sum(n1 >= score - 1e-12)) / 100;
  assert(abs(p1 - expected) < 1e-12, 'sampled p formula');
  g = @(l) nan_unless(l, y);
  [~, ~, p3] = block_permutation_test(g, y, blocks, 'NPermutations', 9, 'Seed', 1);
  assert(p3 == 1, 'NaN null scores count as exceedances');
end


function s = nan_unless(l, y)
  % 1 for the observed labels, NaN for every other arrangement.
  s = NaN;
  if isequal(l, y)
    s = 1;
  end
end


function check_draw()
  blocks = repelem((1:6)', 2);
  y = repelem([1 2 1 2 1 2]', 2);
  [score, null, ~] = block_permutation_test(@(l) l(1), y, blocks, 'Draw', @() [2 1 2 1 2 1]', 'NPermutations', 5);
  assert(score == 1 && numel(null) == 5 && all(null == 2), 'Draw replaces the permutation');
  assert(raises(@() block_permutation_test(@(l) 0, y, blocks, 'Draw', @() [1 2]', 'NPermutations', 2), 'blockperm:draw'), ...
         'Draw must return one label per block');
end


function check_cell_labels()
  blocks = repelem((1:4)', 2);
  y = repelem({'face'; 'house'; 'face'; 'house'}, 2);
  [score, null, p] = block_permutation_test(@(l) double(strcmp(l{1}, 'face')), y, blocks);
  assert(score == 1 && numel(null) == 6 && p > 0, 'cell array labels');
end


function check_size_under_no_information()
  % Labels with no information assigned to blocks at random, drifting data, a refitted nearest-centroid
  % decoder with folds that share blocks: the block test should reject in about 5% of datasets.
  n_data = 200; rejections = 0;
  rng(0, 'twister');
  for d = 1:n_data
    n_blocks = 12; block_len = 10;
    blocks = repelem((1:n_blocks)', block_len);
    drift = cumsum(randn(n_blocks * block_len, 1)) / 5;
    X = [drift + randn(size(drift)), -drift + randn(size(drift))];
    lab = ones(n_blocks, 1); lab(randperm(n_blocks, n_blocks / 2)) = 2;
    y = lab(blocks);
    folds = mod(randperm(numel(y))', 5) + 1;
    f = @(l) centroid_cv_accuracy(X, l, folds);
    [~, ~, p] = block_permutation_test(f, y, blocks, 'NPermutations', 99);
    rejections = rejections + (p < 0.05);
  end
  rate = rejections / n_data;
  fprintf('size under no information: %.3f (%d of %d)\n', rate, rejections, n_data);
  assert(rate >= 0.01 && rate <= 0.11, 'block test size near 0.05 (not inflated, not degenerate)');
end


function acc = centroid_cv_accuracy(X, y, folds)
  correct = 0;
  for k = 1:max(folds)
    te = folds == k; tr = ~te;
    c1 = mean(X(tr & y == 1, :), 1); c2 = mean(X(tr & y == 2, :), 1);
    d1 = sum((X(te, :) - c1) .^ 2, 2); d2 = sum((X(te, :) - c2) .^ 2, 2);
    pred = 1 + (d2 < d1);
    correct = correct + sum(pred == y(te));
  end
  acc = correct / numel(y);
end


function tf = raises(fcn, identifier)
  % True if fcn raises an error with this identifier.
  try
    fcn();
    tf = false;
  catch err
    tf = strcmp(err.identifier, identifier);
  end
end
