import { motion, AnimatePresence } from 'motion/react';
import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { message } from 'antd';

// Check-in / Check-out - Added Return Home flow after successful check-in/out
const RobotCheckinPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [showLiveFeed, setShowLiveFeed] = useState(false);
    const [isIdentified, setIsIdentified] = useState(false);
    const [identifiedUser, setIdentifiedUser] = useState<any>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    
    const isAccompanistMode = location.state?.mode === 'accompanist';

    const liveFeed = [
        {
            name: 'Elara Vance',
            status: 'INBOUND',
            time: '14:15:22 PST',
            isActive: true,
            avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDHuUul5HVhZBHpmd9uwoFgmfaFhddIL8atCAtccxYPuCdtSleTKiy1Rs39DOyK9oRklAPAsI6LRFPd9hq-JW-nZphkT8n1ZZX7Ayl61Lq__4i4TjwW7DLj5tMrKDfp2gXZ1ySqsgfj2u918N3EM1M2v2jEEPv7MsAKV2sQht_Tz5ulo3dgqQ6B1VbBe4KBqPpuArzkqkIE93yVsnv76MaVS_igthFsQmqXYA7sxAB_IPgs_0HD_-pO7uOr0krBBmVpqIkJ5sh1ciB5',
        },
        {
            name: 'Kaelen Thorne',
            status: 'OUTBOUND',
            time: '13:42:05 PST',
            isActive: false,
            avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuB4NXI9QpeqG_saJp-T-JiObj4tLmQ5CEBsRBgWpWbE7kXwjOpMri4C_rH_SyFWF7LgzYyKcuzHImSVXMV2FqmHr80EoKy9OSSsx4Jh4NDb_xpLM4Dy9Hw_3mO4rt890Lb-vGBsB5FM_4c3kQjnj8qVIp8_RYqDvxF2rNY_r5Eo5APMnmLjErnG_kH7X2VrenvhcEoNiWytZV8V00GnUA7o7r5_TVNHl_ZQXPFXWYYMvKYJ8l9Kv8cbSajHvvQ5sAjZCnr7Zy_jRaeR',
        },
        {
            name: 'Nova Quinn',
            status: 'INBOUND',
            time: '12:10:44 PST',
            isActive: true,
            avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAn5FR1yEYkpONRObvvRC75VwVcQZkqaHUu5HPNynrDMxDir8jv1UJz0iE-f9ThXDlP9TSAO3Cc4RC5zQSQVJFCUfZ6EV478dRnYR-PfPRZrHq1Sfr1I7U0zvJBypIcwc31Uqg1yUTAe4RVZ-HdXDd2v6y4-Lm12sF69Fc8xl1j_s1jHa5tUsQtMCm3QpSN2GGxj64yBPBvvzOWcrRlluoUFuAqhj353kXkZ9_00X25SZPNqrrqBx3vUxBwIl4mpyXc8E1EYuXgVF6j',
        },
    ];

    const simulateIdentification = () => {
        setIsIdentified(true);
        setIdentifiedUser(liveFeed[0]);
    };

    const handleAction = (type: 'in' | 'out') => {
        setIsProcessing(true);
        // Simulate API call
        setTimeout(() => {
            setIsProcessing(false);
            message.success(`Clock ${type} successful!`);
            // Return to home after success if not in accompanist mode
            if (!isAccompanistMode) {
                navigate('/dashboard/robot');
            }
        }, 1500);
    };

    return (
        <main className="flex w-full h-[calc(100vh-5rem)] overflow-hidden">
            {/* Scanner Section */}
            <section className="flex-1 flex flex-col items-center justify-center p-10 relative overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(79,219,200,0.05),_#10131a,_#10131a)] -z-10 pointer-events-none" />

                {/* Header Context */}
                <AnimatePresence>
                    {isAccompanistMode ? (
                        <motion.div 
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="absolute top-8 left-10 z-20 flex items-center gap-4 bg-[#4fdbc8]/10 border border-[#4fdbc8]/30 px-6 py-3 rounded-2xl backdrop-blur-md"
                        >
                            <span className="material-symbols-outlined text-[#4fdbc8]">person_add</span>
                            <div>
                                <div className="text-[#4fdbc8] font-bold font-['Space_Grotesk'] text-lg">Accompanist Verification</div>
                                <div className="text-[#c2c6d6] text-xs font-['JetBrains_Mono']">AN EXISTING MEMBER MUST BE IDENTIFIED FIRST</div>
                            </div>
                        </motion.div>
                    ) : (
                        <motion.div 
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="absolute top-8 left-10 z-20 flex items-center gap-4 bg-white/5 border border-white/10 px-6 py-3 rounded-2xl backdrop-blur-md"
                        >
                            <span className="material-symbols-outlined text-[#adc6ff]">qr_code_scanner</span>
                            <div>
                                <div className="text-[#e1e2ec] font-bold font-['Space_Grotesk'] text-lg">Attendance Control</div>
                                <div className="text-[#c2c6d6] text-xs font-['JetBrains_Mono']">SCAN TO CLOCK IN OR OUT</div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Toggle Button for Live Feed */}
                <div className="absolute top-8 right-8 z-20">
                    <button 
                        onClick={() => setShowLiveFeed(!showLiveFeed)}
                        className={`flex items-center gap-2 px-4 h-10 rounded-full border transition-all active:scale-95 ${
                            showLiveFeed 
                            ? 'bg-[#4fdbc8] text-[#003731] border-[#4fdbc8]' 
                            : 'bg-[#191b23]/60 text-[#c2c6d6] border-[#424754]/40 hover:border-[#4fdbc8]/50'
                        }`}
                    >
                        <span className="material-symbols-outlined text-[18px]">
                            {showLiveFeed ? 'visibility_off' : 'monitoring'}
                        </span>
                        <span className="font-['JetBrains_Mono'] text-[10px] tracking-[0.1em] font-bold uppercase">
                            {showLiveFeed ? 'Hide Live Feed' : 'Show Live Feed'}
                        </span>
                    </button>
                </div>

                {/* Scanner Frame */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5 }}
                    onClick={simulateIdentification}
                    className={`relative w-[500px] h-[500px] md:w-[560px] md:h-[560px] flex flex-col items-center justify-center bg-[#191b23]/40 backdrop-blur-xl border rounded-xl mb-12 shadow-[0_0_40px_rgba(79,219,200,0.05)] cursor-pointer group ${
                        isIdentified ? 'border-[#4fdbc8]' : 'border-[#4fdbc8]/20'
                    }`}
                >
                    {/* Corner brackets */}
                    <div className={`absolute top-0 left-0 w-12 h-12 border-t-4 border-l-4 rounded-tl-xl shadow-[0_0_25px_rgba(79,219,200,0.5)] m-[-2px] transition-colors ${isIdentified ? 'border-[#4fdbc8]' : 'border-[#4fdbc8]/50'}`} />
                    <div className={`absolute top-0 right-0 w-12 h-12 border-t-4 border-r-4 rounded-tr-xl shadow-[0_0_25px_rgba(79,219,200,0.5)] m-[-2px] transition-colors ${isIdentified ? 'border-[#4fdbc8]' : 'border-[#4fdbc8]/50'}`} />
                    <div className={`absolute bottom-0 left-0 w-12 h-12 border-b-4 border-l-4 rounded-bl-xl shadow-[0_0_25px_rgba(79,219,200,0.5)] m-[-2px] transition-colors ${isIdentified ? 'border-[#4fdbc8]' : 'border-[#4fdbc8]/50'}`} />
                    <div className={`absolute bottom-0 right-0 w-12 h-12 border-b-4 border-r-4 rounded-br-xl shadow-[0_0_25px_rgba(79,219,200,0.5)] m-[-2px] transition-colors ${isIdentified ? 'border-[#4fdbc8]' : 'border-[#4fdbc8]/50'}`} />

                    {/* Scanning line animation */}
                    {!isIdentified && (
                        <div className="absolute inset-0 overflow-hidden rounded-xl">
                            <div className="absolute left-0 right-0 h-full bg-[linear-gradient(180deg,rgba(79,219,200,0)_0%,rgba(79,219,200,0.05)_50%,rgba(79,219,200,0)_100%)] animate-[scan_3s_ease-in-out_infinite]" />
                        </div>
                    )}

                    {/* Face Icon / Identified User */}
                    <AnimatePresence mode="wait">
                        {!isIdentified ? (
                            <motion.div 
                                key="scanning"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="flex flex-col items-center justify-center text-[#4fdbc8] opacity-80"
                            >
                                <span className="material-symbols-outlined text-[100px] md:text-[120px] font-light mb-6">face</span>
                                <div className="font-['JetBrains_Mono'] text-[10px] md:text-[12px] tracking-[0.2em] animate-pulse">AWAITING SUBJECT IDENTIFICATION...</div>
                                <div className="mt-4 text-[10px] text-[#c2c6d6]/50 uppercase tracking-widest">(Click to simulate ID)</div>
                            </motion.div>
                        ) : (
                            <motion.div 
                                key="identified"
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="flex flex-col items-center justify-center text-[#4fdbc8]"
                            >
                                <div className="relative mb-6">
                                    <img 
                                        src={identifiedUser.avatar} 
                                        className="w-32 h-32 md:w-40 md:h-40 rounded-full border-4 border-[#4fdbc8] object-cover shadow-[0_0_30px_rgba(79,219,200,0.3)]"
                                        alt="Identified"
                                    />
                                    <div className="absolute -bottom-2 -right-2 bg-[#4fdbc8] text-[#003731] w-10 h-10 rounded-full flex items-center justify-center shadow-lg">
                                        <span className="material-symbols-outlined text-2xl font-bold">check</span>
                                    </div>
                                </div>
                                <div className="font-['Space_Grotesk'] text-[24px] md:text-[32px] font-bold text-[#e1e2ec] mb-1">{identifiedUser.name}</div>
                                <div className="font-['JetBrains_Mono'] text-[14px] tracking-[0.1em] uppercase opacity-70">Member Identified Successfully</div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>

                {/* Action Buttons */}
                <div className="flex gap-6 w-full max-w-[560px]">
                    {isAccompanistMode && isIdentified ? (
                        <motion.button
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => navigate('/dashboard/robot/register')}
                            className="flex-1 h-20 bg-[#4fdbc8] text-[#003731] rounded-xl font-['Space_Grotesk'] text-[20px] md:text-[24px] leading-[1.2] font-semibold flex items-center justify-center gap-3 shadow-[0_0_25px_rgba(79,219,200,0.5)] hover:brightness-110 transition-all"
                        >
                            <span className="material-symbols-outlined text-[32px]">arrow_forward</span>
                            Proceed to Registration
                        </motion.button>
                    ) : (
                        <>
                            <motion.button
                                whileHover={isIdentified ? { scale: 1.02 } : {}}
                                whileTap={isIdentified ? { scale: 0.98 } : {}}
                                onClick={() => isIdentified && handleAction('in')}
                                className={`flex-1 h-20 rounded-xl font-['Space_Grotesk'] text-[20px] md:text-[24px] leading-[1.2] font-semibold flex items-center justify-center gap-3 transition-all ${
                                    isIdentified 
                                    ? 'bg-[#4fdbc8] text-[#003731] shadow-[0_0_25px_rgba(79,219,200,0.5)]' 
                                    : 'bg-[#1d2027] border border-[#424754] text-[#e1e2ec] opacity-50 cursor-not-allowed'
                                }`}
                            >
                                {isProcessing ? (
                                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-current"></div>
                                ) : (
                                    <>
                                        <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>how_to_reg</span>
                                        Clock In
                                    </>
                                )}
                            </motion.button>
                            <motion.button
                                whileHover={isIdentified ? { scale: 1.02 } : {}}
                                whileTap={isIdentified ? { scale: 0.98 } : {}}
                                onClick={() => isIdentified && handleAction('out')}
                                className={`flex-1 h-20 rounded-xl font-['Space_Grotesk'] text-[20px] md:text-[24px] leading-[1.2] font-semibold flex items-center justify-center gap-3 transition-all ${
                                    isIdentified
                                    ? 'bg-[#1d2027] border border-[#424754] text-[#e1e2ec] hover:border-[#4fdbc8]/50 hover:bg-[#363941]/50 shadow-[0_0_25px_rgba(0,0,0,0.2)]'
                                    : 'bg-[#1d2027] border border-[#424754] text-[#e1e2ec] opacity-50 cursor-not-allowed'
                                }`}
                            >
                                {isProcessing ? (
                                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-current"></div>
                                ) : (
                                    <>
                                        <span className="material-symbols-outlined">logout</span>
                                        Clock Out
                                    </>
                                )}
                            </motion.button>
                        </>
                    )}
                </div>

                {/* Cancel/Back Button */}
                <div className="mt-8">
                    <button 
                        onClick={() => navigate('/dashboard/robot')}
                        className="text-[#c2c6d6] hover:text-[#e1e2ec] font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] uppercase flex items-center gap-2 transition-colors"
                    >
                        <span className="material-symbols-outlined text-[18px]">close</span>
                        Cancel Operation
                    </button>
                </div>
            </section>

            {/* Live Feed Sidebar */}
            <AnimatePresence>
                {showLiveFeed && (
                    <motion.aside 
                        initial={{ x: 420, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: 420, opacity: 0 }}
                        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                        className="w-[420px] bg-[#0b0e15]/80 backdrop-blur-2xl border-l border-[#424754]/10 p-10 flex flex-col z-10 shadow-[-20px_0_40px_rgba(0,0,0,0.5)]"
                    >
                        <div className="flex items-center justify-between mb-8">
                            <h3 className="font-['Space_Grotesk'] text-[24px] leading-[1.2] font-semibold text-[#4fdbc8]">Live Feed</h3>
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-[#4fdbc8] animate-pulse shadow-[0_0_15px_rgba(79,219,200,0.2)]" />
                                <span className="font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium text-[#4fdbc8] uppercase">Sync Active</span>
                            </div>
                        </div>

                        <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar">
                            {liveFeed.map((person, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.1 }}
                                    className={`bg-[#1d2027] rounded-xl p-4 flex items-center gap-4 relative overflow-hidden flex-shrink-0 ${
                                        person.isActive ? 'border border-[#4fdbc8]/20 shadow-[0_0_15px_rgba(79,219,200,0.2)]' : 'border border-[#424754]/20'
                                    }`}
                                >
                                    <div className={`absolute left-0 top-0 bottom-0 w-1 ${person.isActive ? 'bg-[#4fdbc8]' : 'bg-[#424754]'}`} />
                                    <img
                                        alt="Avatar"
                                        className={`w-14 h-14 rounded-full border object-cover ${
                                            person.isActive ? 'border-[#4fdbc8]/50' : 'border-[#424754]/50 opacity-70'
                                        }`}
                                        src={person.avatar}
                                    />
                                    <div className="flex-1">
                                        <div className={`font-semibold ${person.isActive ? 'text-[#e1e2ec]' : 'text-[#c2c6d6]'}`}>{person.name}</div>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className={`px-2 py-0.5 rounded-full font-['JetBrains_Mono'] text-[10px] ${
                                                person.status === 'INBOUND'
                                                    ? 'bg-[#4fdbc8]/10 border border-[#4fdbc8]/30 text-[#4fdbc8]'
                                                    : 'bg-[#363941] border border-[#424754]/30 text-[#c2c6d6]'
                                            }`}>{person.status}</span>
                                            <span className="font-['JetBrains_Mono'] text-[10px] text-[#8c909f]">{person.time}</span>
                                        </div>
                                    </div>
                                    {person.isActive && (
                                        <span className="material-symbols-outlined text-[#4fdbc8] opacity-50">verified_user</span>
                                    )}
                                </motion.div>
                            ))}
                        </div>

                        <div className="mt-8 pt-6 border-t border-[#424754]/10">
                            <div className="flex items-center justify-between font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] text-[#c2c6d6]">
                                <span>SYSTEM STATUS</span>
                                <span className="text-[#4fdbc8]">OPTIMAL</span>
                            </div>
                        </div>
                    </motion.aside>
                )}
            </AnimatePresence>

            <style>{`
                @keyframes scan {
                    0% { transform: translateY(-100%); }
                    100% { transform: translateY(100%); }
                }
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(79, 219, 200, 0.1);
                    border-radius: 10px;
                }
            `}</style>
        </main>
    );
};

export default RobotCheckinPage;
