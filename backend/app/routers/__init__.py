from . import auth, brain, commands, contracts, exports, playbooks, review, voice

ROUTERS = [
    auth.router,
    playbooks.router,
    contracts.router,
    voice.router,
    review.router,
    exports.router,
    brain.router,
    commands.router,
]
