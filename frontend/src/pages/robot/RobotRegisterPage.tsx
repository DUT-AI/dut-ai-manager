import { useState } from 'react';
import { motion } from 'motion/react';
import { useNavigate } from 'react-router-dom';

// Member Registration (3-step wizard) - converted from new_member_registration_step_1, step_2, success
const RobotRegisterPage = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState<1 | 2 | 3>(1);
    const [formData, setFormData] = useState({
        fullName: '',
        department: '',
        studentId: '',
    });

    // Keypad handler
    const handleKeyPress = (key: string) => {
        if (key === 'del') {
            setFormData(prev => ({ ...prev, studentId: prev.studentId.slice(0, -1) }));
        } else {
            setFormData(prev => ({ ...prev, studentId: prev.studentId + key }));
        }
    };

    // Step 1: Basic Info + Keypad
    const renderStep1 = () => (
        <motion.div
            key="step1"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            className="flex flex-col gap-10"
        >
            {/* Header & Progress */}
            <header className="flex flex-col gap-6">
                <div className="flex justify-between items-end">
                    <div>
                        <h1 className="font-['Space_Grotesk'] text-[24px] md:text-[32px] leading-[1.2] font-semibold text-[#e1e2ec] mb-2">Member Registration</h1>
                        <p className="text-[#c2c6d6]">Identity initialization sequence.</p>
                    </div>
                    <span className="font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium text-[#4fdbc8]">Step 1 of 3</span>
                </div>
                <div className="w-full h-1 bg-[#272a31] rounded-full overflow-hidden">
                    <div className="h-full w-1/3 bg-gradient-to-r from-[#adc6ff] to-[#4fdbc8] shadow-[0_0_10px_rgba(79,219,200,0.5)]" />
                </div>
            </header>

            {/* Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-6">
                {/* Form Inputs */}
                <div className="lg:col-span-7 flex flex-col gap-6 justify-center">
                    {/* Full Name */}
                    <div className="flex flex-col gap-2 group">
                        <label className="font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium text-[#c2c6d6] group-focus-within:text-[#adc6ff] transition-colors">FULL NAME</label>
                        <div className="relative">
                            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[#424754] group-focus-within:text-[#adc6ff] transition-colors">person</span>
                            <input
                                value={formData.fullName}
                                onChange={(e) => setFormData(prev => ({ ...prev, fullName: e.target.value }))}
                                className="w-full h-[44px] pl-12 pr-4 bg-[#1d2027]/20 border border-[#424754]/30 rounded-xl text-[#e1e2ec] focus:outline-none focus:border-[#adc6ff] focus:bg-[#1d2027]/40 focus:ring-1 focus:ring-[#adc6ff]/50 transition-all placeholder:text-[#424754]/50"
                                placeholder="Enter legal name"
                                type="text"
                            />
                        </div>
                    </div>
                    {/* Department */}
                    <div className="flex flex-col gap-2 group">
                        <label className="font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium text-[#c2c6d6] group-focus-within:text-[#adc6ff] transition-colors">DEPARTMENT</label>
                        <div className="relative">
                            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[#424754] group-focus-within:text-[#adc6ff] transition-colors">domain</span>
                            <input
                                value={formData.department}
                                onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
                                className="w-full h-[44px] pl-12 pr-4 bg-[#1d2027]/20 border border-[#424754]/30 rounded-xl text-[#e1e2ec] focus:outline-none focus:border-[#adc6ff] focus:bg-[#1d2027]/40 focus:ring-1 focus:ring-[#adc6ff]/50 transition-all placeholder:text-[#424754]/50"
                                placeholder="e.g. Robotics, AI Ethics"
                                type="text"
                            />
                        </div>
                    </div>
                    {/* Student ID */}
                    <div className="flex flex-col gap-2">
                        <label className="font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium text-[#c2c6d6]">STUDENT ID</label>
                        <div className="relative">
                            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[#4fdbc8]">badge</span>
                            <input
                                value={formData.studentId}
                                readOnly
                                className="w-full h-16 pl-12 pr-4 bg-[#1d2027]/60 border border-[#4fdbc8] shadow-[0_0_15px_rgba(79,219,200,0.15)] rounded-xl font-['Space_Grotesk'] text-[24px] leading-[1.2] font-semibold text-[#4fdbc8] tracking-widest"
                                type="text"
                            />
                            <div className="absolute right-4 top-1/2 -translate-y-1/2 w-2 h-6 bg-[#4fdbc8] animate-pulse" />
                        </div>
                    </div>
                </div>

                {/* Digital Keypad */}
                <div className="lg:col-span-5 flex flex-col justify-center">
                    <div className="bg-[#191b23]/50 backdrop-blur-md rounded-xl p-4 border border-[#424754]/10">
                        <div className="grid grid-cols-3 gap-3">
                            {[1,2,3,4,5,6,7,8,9].map(num => (
                                <button
                                    key={num}
                                    onClick={() => handleKeyPress(String(num))}
                                    className="h-16 rounded-xl bg-[#32353c] hover:bg-[#363941] active:scale-95 transition-all font-['Space_Grotesk'] text-[24px] leading-[1.2] font-semibold text-[#e1e2ec] flex items-center justify-center border border-white/5"
                                >{num}</button>
                            ))}
                            <button
                                onClick={() => handleKeyPress('del')}
                                className="h-16 rounded-xl bg-[#0b0e15]/50 hover:bg-[#ffb4ab]/20 active:scale-95 transition-all text-[#ffb4ab] flex items-center justify-center border border-transparent hover:border-[#ffb4ab]/30"
                            >
                                <span className="material-symbols-outlined">backspace</span>
                            </button>
                            <button
                                onClick={() => handleKeyPress('0')}
                                className="h-16 rounded-xl bg-[#32353c] hover:bg-[#363941] active:scale-95 transition-all font-['Space_Grotesk'] text-[24px] leading-[1.2] font-semibold text-[#e1e2ec] flex items-center justify-center border border-white/5"
                            >0</button>
                            <div className="h-16 rounded-xl bg-[#0b0e15]/50 opacity-50" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="flex justify-end mt-4 pt-6 border-t border-[#424754]/10">
                <button
                    onClick={() => setStep(2)}
                    className="h-[44px] px-8 bg-[#4fdbc8] text-[#003731] rounded-xl font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium flex items-center gap-2 hover:shadow-[0_0_20px_rgba(79,219,200,0.3)] active:scale-95 transition-all"
                >
                    <span>Next Phase</span>
                    <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </button>
            </footer>
        </motion.div>
    );

    // Step 2: QR Scanner
    const renderStep2 = () => (
        <motion.div
            key="step2"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            className="flex flex-col items-center w-full max-w-lg mx-auto"
        >
            <header className="w-full mb-12 text-center">
                <h1 className="font-['Space_Grotesk'] text-[24px] md:text-[32px] leading-[1.2] font-semibold text-[#adc6ff] mb-2 tracking-tight">Step 2: Identity Verification</h1>
                <p className="text-[#c2c6d6] max-w-md mx-auto">Please align your institutional QR code within the frame to authenticate your credentials.</p>
            </header>

            <div className="bg-white/[0.03] backdrop-blur-[12px] border border-white/10 rounded-xl p-8 md:p-12 w-full flex flex-col items-center relative shadow-[0_0_30px_rgba(79,219,200,0.05)]">
                {/* Status Pill */}
                <div className="absolute top-4 right-4 bg-[#4fdbc8]/10 px-3 py-1 rounded-full border border-[#4fdbc8]/20 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-[#4fdbc8] shadow-[0_0_8px_#4fdbc8]" />
                    <span className="font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium text-[#4fdbc8] uppercase">Scanner Active</span>
                </div>

                <div className="mb-8 mt-4 text-center">
                    <span className="material-symbols-outlined text-4xl text-[#c2c6d6] mb-2 block">qr_code_scanner</span>
                </div>

                {/* Viewfinder */}
                <div className="relative w-64 h-64 md:w-80 md:h-80 mb-8 bg-[#191b23]/50 overflow-hidden flex items-center justify-center border border-[#424754]/30">
                    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(54,57,65,0.2),_#10131a)] opacity-50" />
                    {/* Scanner Brackets */}
                    <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-[#4fdbc8] shadow-[0_0_15px_rgba(79,219,200,0.2)]" />
                    <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-[#4fdbc8] shadow-[0_0_15px_rgba(79,219,200,0.2)]" />
                    <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-[#4fdbc8] shadow-[0_0_15px_rgba(79,219,200,0.2)]" />
                    <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-[#4fdbc8] shadow-[0_0_15px_rgba(79,219,200,0.2)]" />
                    {/* Grid */}
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:20px_20px]" />
                    {/* Scan line */}
                    <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-b from-transparent via-[#4fdbc8] to-transparent opacity-50 shadow-[0_0_10px_#4fdbc8]" />
                    <div className="text-[#c2c6d6]/30 font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] text-center px-4">AWAITING CODE DETECT</div>
                </div>

                <div className="text-center space-y-2 mb-8">
                    <p className="font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium text-[#4fdbc8] uppercase">Action Required</p>
                    <p className="text-[#e1e2ec]">Scan your student QR code to verify email</p>
                </div>

                {/* Nav buttons */}
                <div className="flex w-full justify-between gap-4 mt-auto">
                    <button
                        onClick={() => setStep(1)}
                        className="flex-1 h-[44px] border border-[#424754] text-[#e1e2ec] hover:bg-[#363941]/50 transition-colors flex items-center justify-center rounded-sm"
                    >Back</button>
                    <button
                        onClick={() => setStep(3)}
                        className="flex-1 h-[44px] bg-[#adc6ff] text-[#002e6a] hover:bg-[#4d8eff] transition-colors flex items-center justify-center rounded-sm"
                    >Next</button>
                </div>
            </div>

            {/* Progress dots */}
            <div className="mt-12 flex gap-2">
                <div className="w-12 h-1 bg-[#4fdbc8] rounded-full shadow-[0_0_8px_rgba(79,219,200,0.4)]" />
                <div className="w-12 h-1 bg-[#4fdbc8] rounded-full shadow-[0_0_8px_rgba(79,219,200,0.4)]" />
                <div className="w-12 h-1 bg-[#363941] rounded-full" />
            </div>
        </motion.div>
    );

    // Step 3: Success
    const renderStep3 = () => (
        <motion.div
            key="step3"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center w-full max-w-2xl mx-auto"
        >
            {/* Progress Chips */}
            <div className="flex items-center gap-2 mb-12">
                <div className="w-2 h-2 rounded-full bg-[#424754]" />
                <div className="w-8 h-[1px] bg-[#424754]" />
                <div className="w-2 h-2 rounded-full bg-[#424754]" />
                <div className="w-8 h-[1px] bg-[#4fdbc8]/50" />
                <div className="px-3 py-1 rounded-full bg-[#4fdbc8]/10 border border-[#4fdbc8]/30 flex items-center justify-center">
                    <span className="font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium text-[#4fdbc8]">STEP 03 // ACTIVE</span>
                </div>
            </div>

            {/* Success Card */}
            <div className="w-full bg-[#1d2027]/40 backdrop-blur-[12px] border border-white/5 rounded-xl p-8 md:p-16 flex flex-col items-center text-center shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
                {/* Glowing Icon */}
                <div className="relative w-32 h-32 flex items-center justify-center mb-8 rounded-full bg-[#191b23] border border-[#4fdbc8]/20 animate-[pulse-glow_3s_ease-in-out_infinite]">
                    <div className="absolute inset-0 rounded-full border border-[#4fdbc8]/40 animate-[spin_10s_linear_infinite]" />
                    <div className="absolute inset-2 rounded-full border border-dashed border-[#adc6ff]/30 animate-[spin_15s_linear_infinite_reverse]" />
                    <span className="material-symbols-outlined text-[64px] text-[#4fdbc8] drop-shadow-[0_0_15px_rgba(79,219,200,0.8)]" style={{ fontVariationSettings: "'FILL' 1, 'wght' 300" }}>
                        check_circle
                    </span>
                </div>

                <h1 className="font-['Space_Grotesk'] text-[48px] leading-[1.1] tracking-[-0.02em] font-bold text-[#e1e2ec] mb-4">
                    Welcome to the Club
                </h1>
                <p className="text-[#c2c6d6] max-w-md mx-auto mb-12">
                    Your registration is complete. Protocol initiated. Explore the Innovation Space and configure your operational parameters.
                </p>

                <button
                    onClick={() => navigate('/dashboard/robot')}
                    className="group relative inline-flex items-center justify-center h-[44px] px-8 rounded-xl bg-[#4fdbc8] text-[#003731] font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium overflow-hidden transition-all hover:shadow-[0_0_20px_rgba(79,219,200,0.4)] hover:-translate-y-0.5 active:translate-y-0 active:scale-95"
                >
                    <div className="absolute inset-0 w-full h-full bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
                    <span className="relative flex items-center gap-2">
                        <span className="material-symbols-outlined text-[18px]">home</span>
                        Go to Home
                    </span>
                </button>
            </div>

            {/* System Status */}
            <div className="mt-12 flex items-center gap-3 opacity-60">
                <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#4fdbc8] opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[#4fdbc8]" />
                </span>
                <span className="font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium text-[#c2c6d6]">SECURE CONNECTION ESTABLISHED</span>
            </div>
        </motion.div>
    );

    return (
        <main className="min-h-[calc(100vh-5rem)] flex items-center justify-center p-5 md:p-10 relative">
            {/* Ambient background */}
            <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
                <div className="absolute top-[-20%] left-[-10%] w-[50vw] h-[50vw] bg-[#4fdbc8]/5 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[40vw] h-[40vw] bg-[#adc6ff]/5 rounded-full blur-[100px]" />
            </div>

            <div className="w-full max-w-6xl relative z-10">
                {/* Glassmorphic Container for step 1 */}
                {step === 1 && (
                    <div className="bg-[#1d2027]/40 backdrop-blur-xl border border-white/5 rounded-xl p-8 md:p-12 shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                        {renderStep1()}
                    </div>
                )}
                {step === 2 && renderStep2()}
                {step === 3 && renderStep3()}
            </div>

            <style>{`
                @keyframes pulse-glow {
                    0% { box-shadow: 0 0 10px rgba(79, 219, 200, 0.4); }
                    50% { box-shadow: 0 0 30px rgba(79, 219, 200, 0.8), 0 0 60px rgba(79, 219, 200, 0.4); }
                    100% { box-shadow: 0 0 10px rgba(79, 219, 200, 0.4); }
                }
            `}</style>
        </main>
    );
};

export default RobotRegisterPage;
