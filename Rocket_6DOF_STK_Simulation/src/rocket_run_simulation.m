
        % rocket_run_simulation.m -- runs a simple ballistic-like trajectory
        % Educational: uses a very simple point-mass under gravity and constant horizontal speed

        % Load parameters
        D = load(fullfile('..','output','rocket_6dof_params.mat'));
        sim = D.sim; state = D.state;

        % Preallocate
        t = sim.t0:sim.dt:sim.tf;
        N = numel(t);
        lat = zeros(N,1); lon = zeros(N,1); alt = zeros(N,1);

        % Earth radius (mean)
        R_earth = 6371000;

        % Simple model: constant eastward speed, no thrust, ballistic vertical motion with gravity
        vx = state.v0;  % horizontal speed [m/s]
        vy = 0;

        % initial geodetic values
        lat(1) = state.lat0; lon(1) = state.lon0; alt(1) = state.alt0;

        for k=2:N
            % advance simple horizontal motion along constant latitude (educational only)
            dx = vx * sim.dt; % meters east
            dlon = dx / (R_earth * cos(lat(k-1)) );
            lon(k) = lon(k-1) + dlon;
            lat(k) = lat(k-1);

            % simple vertical profile: toy parabolic arc
            tfrac = t(k)/sim.tf;
            alt(k) = 100000 * 4 * tfrac .* (1 - tfrac); % peak ~100 km at t = sim.tf/2
            if alt(k) < 0, alt(k) = 0; end
        end

        % Convert to ECEF positions for export using MATLAB built-in
        % geodetic2ecef requires Mapping Toolbox; if not available, fallback to simple spherical conversion
        try
            [x,y,z] = geodetic2ecef(rad2deg(lat), rad2deg(lon), alt);
        catch
            R = 6371000;
            phi = lat; lambda = lon;
            x = (R + alt).*cos(phi).*cos(lambda);
            y = (R + alt).*cos(phi).*sin(lambda);
            z = (R + alt).*sin(phi);
        end

        % Save trajectory
        traj.time = t'; traj.lat = rad2deg(lat)'; traj.lon = rad2deg(lon)'; traj.alt = alt';
        traj.x = x; traj.y = y; traj.z = z;
        outdir = fullfile('..','output');
        if ~exist(outdir,'dir'), mkdir(outdir); end
        save(fullfile(outdir,'rocket_trajectory_data.mat'),'traj');

        % Also write CSV (time,lat,lon,alt)
        fid = fopen(fullfile(outdir,'rocket_trajectory_data.csv'),'w');
        fprintf(fid,'time_s,lat_deg,lon_deg,alt_m\n');
        for k=1:numel(traj.time)
            fprintf(fid,'%f,%f,%f,%f\n',traj.time(k),traj.lat(k),traj.lon(k),traj.alt(k));
        end
        fclose(fid);

        fprintf('Simulation complete. Outputs in output/ folder.\n');
