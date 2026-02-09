/**
 * PORELIFE: Microbe Survivor
 * Entry Point
 */

(function() {
    window.addEventListener('DOMContentLoaded', function() {
        // Initialize engine
        PL.Engine.initRenderer();
        PL.Engine.input.init();

        // Start game loop
        PL.Engine.start();

        // Prevent context menu on canvas
        document.getElementById('game-canvas').addEventListener('contextmenu', function(e) {
            e.preventDefault();
        });

        // Handle visibility change (pause when tab hidden)
        document.addEventListener('visibilitychange', function() {
            if (document.hidden && PL.Game.getState() === PL.STATE.PLAYING) {
                // Auto-pause handled by frame time clamping
            }
        });

        console.log('PORELIFE: Microbe Survivor');
        console.log('Based on CompLaB3D - Pore-Scale Reactive Transport Research');
        console.log('University of Georgia');
    });
})();
