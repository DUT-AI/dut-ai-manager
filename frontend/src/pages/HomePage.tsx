import { useAuth } from "../context/AuthContext";
import { Typography } from "antd";
const { Title } = Typography;

const HomePage = () => {
    const { user } = useAuth();
    return (
        <div className="max-w-4xl mx-auto py-10 px-6">
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 transition-all hover:shadow-md">
                <Title level={3} className="!mb-6 text-gray-800">
                    Chào mừng quay trở lại, <span className="text-[#6366f1]">{user?.name}</span>!
                </Title>
            </div>
        </div>
    )
}

export default HomePage
