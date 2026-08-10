// WaitWise Toast Notification Handler

window.showInAppNotification = function(notification) {
    console.log("Showing toast notification: ", notification);
    
    // Play sound chime if available
    try {
        const audio = new Audio("https://assets.mixkit.co/active_storage/sfx/2568/2568-84.wav");
        audio.play();
    } catch(e) {
        console.log("Audio alert blocked by browser.");
    }
    
    // Create toast container if it doesn't exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-5 right-5 z-50 flex flex-col space-y-3 max-w-sm w-full';
        document.body.appendChild(container);
    }
    
    // Create toast card
    const toast = document.createElement('div');
    toast.className = 'p-4 rounded-xl border border-brand-500/20 bg-slate-900/90 text-white backdrop-blur-md shadow-2xl transition-all duration-500 transform translate-x-full opacity-0 flex items-start space-x-3';
    
    toast.innerHTML = `
        <div class="bg-brand-500 text-white p-2 rounded-lg text-sm shadow-md">
            <i class="fa-solid fa-bell"></i>
        </div>
        <div class="flex-grow">
            <h4 class="font-bold text-xs text-white">${notification.title}</h4>
            <p class="text-[11px] text-slate-400 mt-1 leading-relaxed">${notification.message}</p>
        </div>
        <button class="text-slate-500 hover:text-slate-100 transition focus:outline-none" onclick="this.parentElement.remove()">
            <i class="fa-solid fa-xmark text-xs"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Trigger entrance animation
    setTimeout(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
    }, 100);
    
    // Auto-remove toast after 7 seconds
    setTimeout(() => {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, 7000);
};
