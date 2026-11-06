
        % since all participants are independent, all chunks are set to
        % unique values
        ds.sa.chunks(:)=1:(ngroups*nchunks);

        % define partitions
        fold_count=50;
        test_count=1;
        partitions=cosmo_independent_samples_partitioner(ds,...
                                'fold_count',fold_count,...
                                'test_count',test_count);

        % define neighborhood
        radius_in_voxels=1; % typical is 3 voxels
        nh=cosmo_spherical_neighborhood(ds,'radius',radius_in_voxels);

        % run searchlight on original data
        opt=struct();
        opt.classifier=@cosmo_classify_lda;
        opt.partitions=partitions;

        result=cosmo_searchlight(ds,nh,...
                            @cosmo_crossvalidation_measure,opt);

        % generate null dataset
        niter=100; % at least 1000 is iterations is recommended, 10000 is better
        ds_null_cell=cell(niter,1);

        for iter=1:niter
            ds_null=ds;

            ds_null.sa.targets=cosmo_randomize_targets(ds_null);

            % update partitions
            opt.partitions=cosmo_independent_samples_partitioner(ds_null,...
                                'fold_count',fold_count,...
                                'test_count',test_count);


            null_result=cosmo_searchlight(ds_null,nh,...
                                    @cosmo_crossvalidation_measure,opt);

            ds_null_cell{iter}=null_result;
        end
        %%

        % Since partitions are balanced, chance level
        % is the inverse of the number of groups. For example,
        % with 4 groups, chance level is 1/4 = 0.25 = 25%.
        chance_level=1/ngroups;
        tfce_dh=0.01; % should be sufficient for accuracies
