import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';

import RobotHomePage from './robot/RobotHomePage';
import RobotActivityPage from './robot/RobotActivityPage';
import RobotCheckinPage from './robot/RobotCheckinPage';
import RobotRegisterPage from './robot/RobotRegisterPage';

// Shared top nav bar for the Robot Interface - Enhanced with Dynamic Battery & Network Status
const RobotTopNav = () => {
    const [time, setTime] = useState('');
    const [batteryLevel, setBatteryLevel] = useState<number | null>(null);
    const [isCharging, setIsCharging] = useState(false);
    const [isOnline, setIsOnline] = useState(navigator.onLine);
    
    const navigate = useNavigate();
    const location = useLocation();

    const isRobotHome = location.pathname === '/dashboard/robot' || location.pathname === '/dashboard/robot/';

    useEffect(() => {
        // Time update
        const updateTime = () => {
            const now = new Date();
            setTime(now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }));
        };
        updateTime();
        const timeInterval = setInterval(updateTime, 1000);

        // Battery Status
        if ('getBattery' in navigator) {
            (navigator as any).getBattery().then((battery: any) => {
                const updateBattery = () => {
                    setBatteryLevel(Math.round(battery.level * 100));
                    setIsCharging(battery.charging);
                };
                updateBattery();
                battery.addEventListener('levelchange', updateBattery);
                battery.addEventListener('chargingchange', updateBattery);
            });
        }

        // Network Status
        const handleOnline = () => setIsOnline(true);
        const handleOffline = () => setIsOnline(false);
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            clearInterval(timeInterval);
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    const handleBack = () => {
        if (isRobotHome) {
            navigate('/dashboard');
        } else {
            navigate('/dashboard/robot');
        }
    };

    const getBatteryIcon = () => {
        if (isCharging) return 'battery_charging_full';
        if (batteryLevel === null) return 'battery_unknown';
        if (batteryLevel > 90) return 'battery_full';
        if (batteryLevel > 70) return 'battery_6_bar';
        if (batteryLevel > 50) return 'battery_4_bar';
        if (batteryLevel > 20) return 'battery_2_bar';
        return 'battery_alert';
    };

    return (
        <header className="bg-[#10131a]/60 backdrop-blur-xl fixed top-0 w-full border-b border-[#424754]/10 shadow-[0_0_20px_rgba(79,219,200,0.1)] flex justify-between items-center h-20 px-6 z-50">
            <div className="flex items-center gap-4">
                <button 
                    onClick={handleBack}
                    className="hover:bg-[#4fdbc8]/10 transition-colors p-2 rounded-full active:scale-95 group mr-2"
                    title={isRobotHome ? "Back to Dashboard" : "Back to Robot Home"}
                >
                    <span className="material-symbols-outlined text-[#4fdbc8] group-hover:scale-110 transition-transform">
                        {isRobotHome ? 'dashboard' : 'arrow_back'}
                    </span>
                </button>
                <span className="material-symbols-outlined text-[#4fdbc8]" style={{ fontVariationSettings: "'FILL' 1" }}>hexagon</span>
                <h1 className="font-['Space_Grotesk'] text-[24px] md:text-[32px] leading-[1.2] font-bold text-[#4fdbc8] tracking-tighter hidden sm:block">HR Robot</h1>
            </div>
            <div className="flex items-center gap-6">
                <span className="font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] text-[#c2c6d6] hidden md:block">{time}</span>
                <div className="flex gap-4 items-center">
                    {/* Dynamic Battery Icon */}
                    <div className="flex items-center gap-1.5 hover:bg-[#4fdbc8]/10 transition-colors px-3 py-1.5 rounded-full" title={`Battery: ${batteryLevel}% ${isCharging ? '(Charging)' : ''}`}>
                        <span className={`material-symbols-outlined text-[20px] ${batteryLevel !== null && batteryLevel < 20 && !isCharging ? 'text-red-500 animate-pulse' : 'text-[#4fdbc8]'}`}>
                            {getBatteryIcon()}
                        </span>
                        {batteryLevel !== null && (
                            <span className="font-['JetBrains_Mono'] text-[10px] font-bold text-[#c2c6d6]">{batteryLevel}%</span>
                        )}
                    </div>

                    {/* Dynamic WiFi/Network Icon */}
                    <div className="flex items-center hover:bg-[#4fdbc8]/10 transition-colors p-2 rounded-full" title={isOnline ? 'Online' : 'Offline'}>
                        <span className={`material-symbols-outlined text-[20px] ${isOnline ? 'text-[#4fdbc8]' : 'text-red-500'}`}>
                            {isOnline ? 'wifi' : 'wifi_off'}
                        </span>
                    </div>
                </div>
            </div>
        </header>
    );
};

const RobotInterfacePage = () => {
    const location = useLocation();

    return (
        <div className="min-h-screen bg-[#0B1120] text-[#e1e2ec] font-['Inter'] antialiased overflow-x-hidden">
            {/* Google Fonts */}
            <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
            <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />

            <RobotTopNav />

            <div className="pt-20">
                <Routes>
                    <Route index element={<RobotHomePage />} />
                    <Route path="activity" element={<RobotActivityPage />} />
                    <Route path="checker" element={<RobotCheckinPage />} />
                    <Route path="register" element={<RobotRegisterPage />} />
                </Routes>
            </div>
        </div>
    );
};

export default RobotInterfacePage;
