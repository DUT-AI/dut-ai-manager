import { motion } from 'motion/react';
import { ReactNode } from 'react';

interface PageWrapperProps {
    children: ReactNode;
    className?: string;
}

const pageVariants = {
    initial: {
        opacity: 0,
        y: 10,
    },
    animate: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.4,
            ease: "easeOut",
            staggerChildren: 0.1,
        },
    },
    exit: {
        opacity: 0,
        y: -10,
        transition: {
            duration: 0.3,
        },
    },
};

export const PageWrapper = ({ children, className }: PageWrapperProps) => {
    return (
        <motion.div
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={className}
        >
            {children}
        </motion.div>
    );
};

export const MotionItem = ({ children, className }: PageWrapperProps) => {
    return (
        <motion.div
            variants={{
                initial: { opacity: 0, y: 20 },
                animate: { opacity: 1, y: 0 }
            }}
        >
            {children}
        </motion.div>
    );
};
