        % rocket_6dof_main.m -- educational initialization (non-operational)
        clearvars; close all; clc;
        project_root = fileparts(mfilename('fullpath'));
        cd(project_root);

        % Launch / simulation settings (simple, educational only)
        sim.t0 = 0;                  % start time [s]
        sim.tf = 300;                % final time [s]
        sim.dt = 1.0;                % time step [s]

        % Simple "vehicle" properties (non-weaponized placeholders)
        vehicle.mass = 1000;         % kg (placeholder)
        vehicle.length = 5;          % m

        % Initial state: latitude, longitude, altitude, vel_ned
        state.lat0 = 28.5*pi/180;   % radians
        state.lon0 = -80.5*pi/180;  % radians
        state.alt0 = 0;             % m
        state.v0 = 500;             % m/s eastwards (placeholder)

        outdir = fullfile('..','output');
        if ~exist(outdir,'dir'), mkdir(outdir); end

        save(fullfile(outdir,'rocket_6dof_params.mat'),'sim','vehicle','state');
        fprintf('Initialization complete. Parameters saved to output/.\n');
