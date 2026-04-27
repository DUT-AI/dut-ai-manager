import { Modal, Form, Select, TimePicker, Input } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import type { PermissionRequestResponse } from '@/types/activity.types';
import type { Homework } from '@/types/homework.types';
import type { MeetingResponse } from '@/types/meeting.types';

const { Option } = Select;
const { TextArea } = Input;

interface Props {
    open: boolean;
    editingItem: PermissionRequestResponse | null;
    initialDate: Dayjs;
    homeworks: Homework[];
    meetings: MeetingResponse[];
    onSubmit: (values: any) => void;
    onCancel: () => void;
}

export const PermissionRequestModal = ({ open, editingItem, initialDate, homeworks, meetings, onSubmit, onCancel }: Props) => {
    const [form] = Form.useForm();

    const initialValues = editingItem ? {
        category: editingItem.category,
        note: editingItem.note,
        homework_id: editingItem.homework_id,
        meeting_id: editingItem.meeting_id,
        start_time: editingItem.start_time ? dayjs(editingItem.start_time) : null,
    } : { start_time: initialDate };

    const handleFinish = (values: any) => {
        let finalStartTime = undefined;
        if (values.start_time) {
            // Since this modal creates from a specific date day, we maintain that date part
            const dateStr = initialDate.format('YYYY-MM-DD');
            const timeStr = values.start_time.format('HH:mm:ss');
            finalStartTime = `${dateStr}T${timeStr}`;
        }
        
        const formattedValues = {
            ...values,
            start_time: finalStartTime,
        };
        onSubmit(formattedValues);
    };

    return (
        <Modal
            title={editingItem ? "Sửa đơn xin phép" : "Tạo đơn xin phép"}
            open={open}
            onCancel={onCancel}
            onOk={form.submit}
            destroyOnClose
        >
            <Form form={form} initialValues={initialValues} layout="vertical" onFinish={handleFinish}>
                <Form.Item name="category" label="Loại" rules={[{ required: true }]}>
                    <Select onChange={() => form.setFieldsValue({ homework_id: undefined, meeting_id: undefined })}>
                        <Option value="ABSENCE">Vắng sinh hoạt</Option>
                        <Option value="POSTPONE">Tạm hoãn bài tập</Option>
                        <Option value="LATE">Đi trễ sinh hoạt</Option>
                        <Option value="OTHER">Khác</Option>
                    </Select>
                </Form.Item>

                <Form.Item
                    noStyle
                    shouldUpdate={(prevValues, currentValues) => prevValues.category !== currentValues.category}
                >
                    {({ getFieldValue }) => {
                        const category = getFieldValue('category');
                        if (category === 'POSTPONE') {
                            return (
                                <Form.Item name="homework_id" label="Bài tập" rules={[{ required: true, message: 'Vui lòng chọn bài tập!' }]}>
                                    <Select placeholder="Chọn bài tập">
                                        {(homeworks || []).map((hw) => (
                                            <Option key={hw.id} value={hw.id}>{hw.title}</Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            );
                        }
                        if (category === 'ABSENCE' || category === 'LATE') {
                            return (
                                <Form.Item name="meeting_id" label="Buổi sinh hoạt" rules={[{ required: true, message: 'Vui lòng chọn buổi sinh hoạt!' }]}>
                                    <Select placeholder="Chọn buổi sinh hoạt">
                                        {(meetings || []).map((m) => (
                                            <Option key={m.id} value={m.id}>{m.title} ({dayjs(m.start_time).format('DD/MM/YYYY')})</Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            );
                        }
                        return null;
                    }}
                </Form.Item>

                <div className="grid grid-cols-1 gap-4">
                    <Form.Item
                        noStyle
                        shouldUpdate={(prevValues, currentValues) => prevValues.category !== currentValues.category}
                    >
                        {({ getFieldValue }) => {
                            const category = getFieldValue('category');
                            if (category === 'ABSENCE' || category === 'OTHER') return null;

                            if (category === 'POSTPONE') {
                                return (
                                    <Form.Item
                                        name="start_time"
                                        label="Hạn chót mới"
                                        rules={[
                                            { required: true, message: 'Vui lòng chọn thời gian!' },
                                            ({ getFieldValue: getFieldValueForm }) => ({
                                                validator(_, value) {
                                                    const hwId = getFieldValueForm('homework_id');
                                                    if (value && hwId) {
                                                        const homework = homeworks.find((h) => h.id === hwId);
                                                        if (homework) {
                                                            const deadline = dayjs(homework.deadline);
                                                            const diffDays = value.diff(deadline, 'day', true);
                                                            if (diffDays > 4) {
                                                                return Promise.reject(new Error('Thời gian hoãn không được quá 4 ngày!'));
                                                            }
                                                            if (diffDays < 0) {
                                                                return Promise.reject(new Error('Hạn mới phải sau deadline gốc!'));
                                                            }
                                                        }
                                                    }
                                                    return Promise.resolve();
                                                },
                                            }),
                                        ]}
                                    >
                                        <TimePicker format="HH:mm" className="w-full" />
                                    </Form.Item>
                                );
                            }

                            return (
                                <Form.Item name="start_time" label="Thời gian / Hạn chót" rules={[{ required: true, message: 'Vui lòng chọn thời gian!' }]}>
                                    <TimePicker format="HH:mm" className="w-full" />
                                </Form.Item>
                            );
                        }}
                    </Form.Item>
                </div>
                <Form.Item name="note" label="Lý do / Ghi chú" rules={[{ required: true }]}>
                    <TextArea rows={3} />
                </Form.Item>
            </Form>
        </Modal>
    );
};
