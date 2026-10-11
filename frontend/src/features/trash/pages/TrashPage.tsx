import React from 'react';
import { Navigate } from 'react-router-dom';

export const TrashPage: React.FC = () => {
    return <Navigate to="/dashboard/trash/bonus-point" replace />;
};

export default TrashPage;
