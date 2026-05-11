import { motion } from 'motion/react';
import { useNavigate } from 'react-router-dom';

// Home Screen - converted from robot_tablet_home_screen/code.html
const RobotHomePage = () => {
    const navigate = useNavigate();

    const actions = [
        {
            title: 'Activity Registration',
            icon: 'calendar_month',
            onClick: () => navigate('/dashboard/robot/activity'),
        },
        {
            title: 'Register New Member',
            icon: 'person_add',
            onClick: () => navigate('/dashboard/robot/checker', { state: { mode: 'accompanist' } }),
        },
        {
            title: 'Check in / Check out',
            icon: 'qr_code_scanner',
            onClick: () => navigate('/dashboard/robot/checker'),
        },
    ];

    return (
        <main className="flex-1 flex flex-col justify-center items-center px-10 min-h-[calc(100vh-5rem)]">
            {/* Radial gradient background */}
            <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_-20%,_rgba(79,219,200,0.15),_transparent_60%)] pointer-events-none" />

            {/* Welcome Area */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="text-center mb-16 max-w-4xl relative z-10"
            >
                <h1 className="font-['Space_Grotesk'] text-[48px] leading-[1.1] tracking-[-0.02em] font-bold text-[#e1e2ec] mb-4">
                    Welcome to the Innovation Space
                </h1>
                <p className="font-['Space_Grotesk'] text-[32px] leading-[1.2] font-normal text-[#c2c6d6]">
                    How can I help you today?
                </p>
            </motion.div>

            {/* Primary Actions (Bento/Card Layout) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-6xl relative z-10">
                {actions.map((action, idx) => (
                    <motion.button
                        key={idx}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2 + idx * 0.1, duration: 0.4 }}
                        whileHover={{ 
                            boxShadow: '0 0 15px rgba(79, 219, 200, 0.2)',
                            borderColor: 'rgba(79, 219, 200, 0.5)'
                        }}
                        whileTap={{ 
                            boxShadow: '0 0 25px rgba(79, 219, 200, 0.4)',
                            scale: 0.98 
                        }}
                        onClick={action.onClick}
                        className="bg-white/[0.03] backdrop-blur-[12px] border border-white/10 rounded-[24px] p-8 flex flex-col items-center justify-center gap-6 h-64 transition-all duration-300 group focus:outline-none"
                    >
                        <div className="w-20 h-20 rounded-full bg-[#4fdbc8]/10 flex items-center justify-center group-hover:bg-[#4fdbc8]/20 transition-colors">
                            <span className="material-symbols-outlined text-[48px] text-[#4fdbc8]" style={{ fontVariationSettings: "'FILL' 1" }}>
                                {action.icon}
                            </span>
                        </div>
                        <span className="font-['Space_Grotesk'] text-[24px] leading-[1.2] font-semibold text-[#e1e2ec]">
                            {action.title}
                        </span>
                    </motion.button>
                ))}
            </div>
        </main>
    );
};

export default RobotHomePage;
