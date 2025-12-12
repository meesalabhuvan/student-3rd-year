
        % export_to_stk.m -- write a minimal STK .e ephemeris file (ICRF-like header)
        % This is a simplified ephemeris writer for visualization only.

        trajfile = fullfile('..','output','rocket_trajectory_data.mat');
        if ~exist(trajfile,'file')
            error('Trajectory not found. Run rocket_run_simulation first.');
        end
        D = load(trajfile);
        traj = D.traj;

        % Create a simple STK ".e" file in an inertial-like format (time in seconds since epoch)
        epoch = '2025-12-12T00:00:00.000';
        filename = fullfile('..','output','rocket_trajectory.e');
        fid = fopen(filename,'w');
        fprintf(fid,'stk.v.10.0\n\n');
        fprintf(fid,'BEGIN Ephemeris\n\n');
        fprintf(fid,'NumberOfEphemerisPoints %d\n', numel(traj.time));
        fprintf(fid,'CoordinateSystem ICRF\n');
        fprintf(fid,'ScenarioEpoch %s\n', epoch);
        fprintf(fid,'InterpolationOrder 1\n');
        fprintf(fid,'CentralBody Earth\n\n');
        fprintf(fid,'EphemerisTimePosVel\n\n');

        % Write as epoch seconds + position (m) using ECEF values as placeholder
        for k=1:numel(traj.time)
            tsec = traj.time(k);
            fprintf(fid,'%f %f %f %f\n', tsec, traj.x(k), traj.y(k), traj.z(k));
        end

        fprintf(fid,'END Ephemeris\n');
        fclose(fid);
        fprintf('STK ephemeris written to %s\n', filename);
