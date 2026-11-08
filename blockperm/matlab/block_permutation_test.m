function [score, null, p] = block_permutation_test(score_fcn, y, blocks, varargin)
%BLOCK_PERMUTATION_TEST Significance of a cross-validated score by permuting labels between blocks.
%
%   [score, null, p] = block_permutation_test(score_fcn, y, blocks)
%   [score, null, p] = block_permutation_test(..., 'NPermutations', 1000, 'Strata', s, 'Draw', f, ...
%                                             'Exact', 'auto', 'Seed', 0)
%
%   MATLAB counterpart of blockperm.block_permutation_test_score (Python). The labels of whole blocks are
%   permuted between blocks, so the labels of training and test trials move together, and score_fcn is called
%   again for every permuted label vector.
%
%   score_fcn  function handle, score_fcn(labels) -> cross-validated score (higher is better). It must run the
%              whole analysis on the given labels: folds, scaling, feature selection and the classifier are all
%              fitted again inside it. Keep the folds fixed across calls, or let them depend only on labels.
%   y          labels, one per trial (numeric vector or cell array of char), constant within each block.
%   blocks     block identity of each trial (numeric vector or cell array of char).
%
%   Options
%   'NPermutations'  number of sampled permutations (default 1000; ignored when the exact enumeration is used).
%   'Strata'         one value per trial, constant within blocks: labels are permuted only between blocks of
%                    the same stratum. Use the unit the design randomized over (for example runs).
%   'Draw'           function handle, Draw() -> one label per block (order of unique(blocks)); replaces the
%                    permutation, for example to draw pseudosessions from the task's own block generator.
%                    Draw should use the global random stream, so that 'Seed' also fixes its draws.
%   'Exact'          'auto' (default) enumerates all distinct arrangements when there are no more of them than
%                    NPermutations; true forces it (at most 100,000); false always samples.
%   'Seed'           seed for the random permutations (default: the current random state is used).
%
%   score   observed score.
%   null    scores under the null. With the exact enumeration it has one score per arrangement, the observed
%           arrangement included with its observed score.
%   p       sampled: (1 + #{null >= score} + #{null NaN}) / (numel(null) + 1).
%           exact:   (1 + #{other arrangements with score >= observed or NaN}) / (number of arrangements).
%
%   Validity: the enumerated null is exact, and the sampled p valid, when the observed assignment of labels to
%   blocks was drawn uniformly from the arrangements the function permutes over. With a fixed block order the
%   test assumes that blocks are exchangeable under the null; slow drift that follows the order can break this.
%   With two blocks per class there are 6 arrangements, and for a refitted two-class classifier an arrangement
%   and its class swap give the same score, so p cannot fall below about 1/3.

  opt = parse_options(varargin{:});
  [codes, names] = label_codes(y);
  [block_codes, pos] = block_labels_of(codes, blocks);
  if isempty(opt.Strata)
    groups = {(1:numel(block_codes))'};
  else
    groups = strata_groups(block_labels_of(label_codes(opt.Strata), blocks));
  end

  score = score_fcn(y);
  if ~isfinite(score)
    warning('blockperm:undefined', 'the observed score is undefined; p is NaN and no null was computed');
    null = zeros(0, 1);
    p = NaN;
    return
  end

  use_exact = false;
  if isempty(opt.Draw)
    n_arr = n_distinct_arrangements(block_codes, groups);
    use_exact = isequal(opt.Exact, true) || (ischar(opt.Exact) && n_arr <= opt.NPermutations);
    if n_arr < 20
      hint = '';
      if ~use_exact
        hint = '; consider ''Exact'', true';
      end
      warning('blockperm:fewArrangements', ['only %d distinct block-label arrangements: with exact enumeration ' ...
              'p cannot fall below %.3g, and not below %.3g when swapping the two classes leaves the score ' ...
              'unchanged (a refit two-class classifier with balanced blocks)%s'], n_arr, 1 / n_arr, 2 / n_arr, hint);
    end
  end

  if use_exact
    if n_arr > 100000
      error('blockperm:tooMany', 'too many arrangements to enumerate (%d)', n_arr);
    end
    arrangements = enumerate_arrangements(block_codes, groups);
    is_observed = all(arrangements == block_codes(:)', 2);
    null = zeros(size(arrangements, 1), 1);
    null(is_observed) = score;
    for k = find(~is_observed)'
      null(k) = score_fcn(labels_from_codes(arrangements(k, pos), names, y));
    end
    p = (1 + n_at_least(null(~is_observed), score)) / numel(null);
    return
  end

  if ~isempty(opt.Seed)
    rng(opt.Seed, 'twister');
  end
  null = zeros(opt.NPermutations, 1);
  for k = 1:opt.NPermutations
    if isempty(opt.Draw)
      permuted_codes = permute_within(block_codes, groups);
      permuted = labels_from_codes(permuted_codes(pos), names, y);
    else
      [drawn, drawn_names] = label_codes(opt.Draw());
      if numel(drawn) ~= numel(block_codes)
        error('blockperm:draw', 'Draw must return one label per block');
      end
      permuted = labels_from_codes(drawn(pos), drawn_names, y);
    end
    null(k) = score_fcn(permuted);
  end
  p = (1 + n_at_least(null, score)) / (numel(null) + 1);
end


function n = n_at_least(null, score)
  % Null scores at least the observed one; NaN counts (a NaN comparison is false).
  n = sum(~(null < score - 1e-12));
end


function opt = parse_options(varargin)
  opt = struct('NPermutations', 1000, 'Strata', [], 'Draw', [], 'Exact', 'auto', 'Seed', []);
  if mod(numel(varargin), 2)
    error('blockperm:options', 'options must be name-value pairs');
  end
  for k = 1:2:numel(varargin)
    name = varargin{k};
    if ~ischar(name) || ~isfield(opt, name)
      error('blockperm:options', 'unknown option %s', num2str(name));
    end
    opt.(name) = varargin{k + 1};
  end
  n = opt.NPermutations;
  if ~isscalar(n) || n < 1 || n ~= round(n)
    error('blockperm:options', 'NPermutations must be an integer of at least 1');
  end
  if ~(isequal(opt.Exact, 'auto') || isequal(opt.Exact, true) || isequal(opt.Exact, false))
    error('blockperm:options', 'Exact must be ''auto'', true or false');
  end
end


function [codes, names] = label_codes(v)
  % Integer code of each value (1..k, in sorted order) and the sorted distinct values.
  [names, ~, codes] = unique(v(:));
  codes = codes(:);
end


function v = labels_from_codes(codes, names, template)
  % Labels in the type and shape of template.
  v = reshape(names(codes(:)), size(template));
end


function [block_codes, pos] = block_labels_of(codes, blocks)
  % One code per block (order of unique(blocks)) and the position of each trial's block.
  [~, ~, pos] = unique(blocks(:));
  if numel(pos) ~= numel(codes)
    error('blockperm:length', 'labels and blocks must have the same length');
  end
  block_codes = accumarray(pos, codes, [], @min);
  bad = find(accumarray(pos, codes, [], @max) ~= block_codes, 1);
  if ~isempty(bad)
    error('blockperm:notConstant', 'labels must be constant within blocks (block %d holds more than one label)', bad);
  end
end


function groups = strata_groups(strata_codes)
  % Indices of the blocks in each stratum.
  levels = unique(strata_codes);
  groups = cell(1, numel(levels));
  for k = 1:numel(levels)
    groups{k} = find(strata_codes == levels(k));
  end
end


function n = n_distinct_arrangements(block_codes, groups)
  % Product over strata of the multinomial coefficient; computed in logs, so it does not overflow or warn.
  log_n = 0;
  for g = groups
    counts = accumarray(block_codes(g{1}), 1);
    log_n = log_n + gammaln(numel(g{1}) + 1) - sum(gammaln(counts + 1));
  end
  n = round(exp(log_n));
end


function out = permute_within(block_codes, groups)
  out = block_codes;
  for g = groups
    i = g{1};
    out(i) = block_codes(i(randperm(numel(i))));
  end
end


function A = enumerate_arrangements(block_codes, groups)
  % All distinct block-code vectors reachable by permuting within strata (observed one included), one per row.
  A = block_codes(:)';
  for g = groups
    i = g{1};
    perms_i = multiset_permutations(block_codes(i));
    n_old = size(A, 1);
    n_new = size(perms_i, 1);
    A = A(repelem((1:n_old)', n_new), :);
    A(:, i) = repmat(perms_i, n_old, 1);
  end
end


function P = multiset_permutations(items)
  % Distinct orderings of items (with repeated values), one per row, in lexicographic order.
  row = sort(items(:))';
  n = numel(row);
  counts = accumarray(row(:), 1);
  P = zeros(round(exp(gammaln(n + 1) - sum(gammaln(counts + 1)))), n);
  P(1, :) = row;
  for r = 2:size(P, 1)
    % next lexicographic permutation
    k = find(row(1:end - 1) < row(2:end), 1, 'last');
    l = find(row > row(k), 1, 'last');
    row([k, l]) = row([l, k]);
    row(k + 1:end) = fliplr(row(k + 1:end));
    P(r, :) = row;
  end
end
