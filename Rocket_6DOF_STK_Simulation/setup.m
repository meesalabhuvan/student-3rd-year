        % setup.m -- create folder structure and add paths
        root = pwd;
        folders = {'src','docs','output','tests','examples'};
        for i=1:numel(folders)
            if ~exist(folders{i},'dir')
                mkdir(folders{i});
            end
        end
        addpath(genpath(root));
        fprintf('Project folders created and paths added.\n');
