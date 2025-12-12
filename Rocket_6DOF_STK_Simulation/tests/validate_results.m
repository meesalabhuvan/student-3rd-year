\
        % validate_results.m -- basic checks for outputs
        ok = true;
        if ~exist(fullfile('..','output','rocket_trajectory_data.mat'),'file')
            warning('Trajectory MAT file missing.'); ok = false; end
        if ~exist(fullfile('..','output','rocket_trajectory.e'),'file')
            warning('STK ephemeris missing.'); ok = false; end

        if ok
            fprintf('All checks passed: required output files exist.\n');
        else
            fprintf('Some checks failed. See warnings above.\n');
        end
