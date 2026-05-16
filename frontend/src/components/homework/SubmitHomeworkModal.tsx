import { useEffect, useState } from 'react';
import { Modal, Card, Statistic, Typography, message, Upload, Button } from 'antd';
import { FileZipOutlined, DownloadOutlined } from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';
import dayjs from 'dayjs';
import type { Homework, HomeworkSubmission } from '@/types/homework.types';
import { HomeworkStatus } from '@/types/homework.types';
import { homeworkService } from '@/services/api/homework.service';
import { FeedbackModal } from './FeedbackModal';

const { Text, Link } = Typography;

// Allowed file extensions (10MB max)
const ALLOWED_EXTENSIONS = ['.zip', '.rar', '.7z', '.tar.gz', '.gz'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

interface Props {
    open: boolean;
    homework: Homework | null;
    onSuccess: () => void;
    onCancel: () => void;
}

export const SubmitHomeworkModal = ({ open, homework, onSuccess, onCancel }: Props) => {
    const [mySubmission, setMySubmission] = useState<HomeworkSubmission | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [fileList, setFileList] = useState<UploadFile[]>([]);
    const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);

    useEffect(() => {
        if (open && homework) {
            setMySubmission(null);
            setFileList([]);
            fetchMySubmission();
        }
    }, [open, homework]);

    const fetchMySubmission = async () => {
        if (!homework) return;
        try {
            const submission = await homeworkService.getMySubmission(homework.id);
            if (submission) {
                setMySubmission(submission);
            }
        } catch (error: any) {
            // Ignore 404 - user hasn't submitted yet
        }
    };

    const validateFile = (file: File): string | null => {
        const fileName = file.name.toLowerCase();
        const isValidExtension = ALLOWED_EXTENSIONS.some(ext => fileName.endsWith(ext));
        if (!isValidExtension) {
            return `Chỉ chấp nhận file nén: ${ALLOWED_EXTENSIONS.join(', ')}`;
        }
        if (file.size > MAX_FILE_SIZE) {
            return `File quá lớn. Giới hạn tối đa: ${MAX_FILE_SIZE / (1024 * 1024)}MB`;
        }
        return null;
    };

    const handleUploadProps: UploadProps = {
        beforeUpload: (file) => {
            const error = validateFile(file);
            if (error) {
                message.error(error);
                return Upload.LIST_IGNORE;
            }
            setFileList([file as unknown as UploadFile]);
            return false; // Prevent auto upload
        },
        onRemove: () => {
            setFileList([]);
        },
        fileList,
        maxCount: 1,
        accept: ALLOWED_EXTENSIONS.join(','),
    };

    const handleSubmit = async () => {
        if (!homework) return;

        if (fileList.length === 0) {
            message.warning('Vui lòng chọn file để nộp bài');
            return;
        }

        const file = fileList[0] as unknown as File;

        setSubmitting(true);
        try {
            await homeworkService.submit(homework.id, file);
            message.success('Nộp bài thành công');
            onSuccess();
        } catch (error: any) {
            message.error(error?.response?.data?.message || error?.message || 'Nộp bài thất bại');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Modal
            title={`Nộp bài: ${homework?.title}`}
            open={open}
            onCancel={onCancel}
            onOk={handleSubmit}
            okText="Nộp bài"
            confirmLoading={submitting}
            destroyOnClose
            okButtonProps={{ disabled: fileList.length === 0 }}
        >
            {homework && (
                <div className="mb-4">
                    <div className="bg-gray-50 p-3 rounded mb-4">
                        <Text strong>Đề bài:</Text>
                        <div className="whitespace-pre-wrap mt-1 text-gray-700">
                            {homework.description}
                        </div>
                        <div className="mt-2 text-xs text-red-500">
                            Deadline: {dayjs(homework.deadline).format('DD/MM/YYYY HH:mm')}
                        </div>
                        {homework.file_url && (
                            <div className="mt-2 text-xs">
                                <Link href={homework.file_url} target="_blank">
                                    <DownloadOutlined /> Tải file đính kèm
                                </Link>
                            </div>
                        )}
                    </div>

                    {mySubmission && (
                        <Card size="small" className="mb-4 border-blue-200 bg-blue-50">
                            <Statistic
                                title="Trạng thái hiện tại"
                                value={
                                    mySubmission.status === HomeworkStatus.NOT_SUBMITTED ? 'Chưa nộp' :
                                    mySubmission.status === HomeworkStatus.SUBMITTED ? 'Đã nộp' :
                                    mySubmission.status === HomeworkStatus.LeaderChecked ? 'Leader Check' :
                                    mySubmission.status === HomeworkStatus.FINISHED ? 'Hoàn thành' : mySubmission.status
                                }
                                valueStyle={{ fontSize: 16, color: '#1890ff' }}
                            />
                            <div className="mt-2">
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    Cập nhật lần cuối: {dayjs(mySubmission.updated_at).format('DD/MM HH:mm')}
                                </Text>
                                {mySubmission.link && (
                                    <div className="mt-1">
                                        <Link href={mySubmission.link} target="_blank">
                                            <DownloadOutlined /> Tải file đã nộp
                                        </Link>
                                    </div>
                                )}
                                {(mySubmission.status === HomeworkStatus.SUBMITTED || mySubmission.status === HomeworkStatus.LeaderChecked || mySubmission.status === HomeworkStatus.FINISHED) && (
                                    <div className="mt-3">
                                        <Button
                                            type="primary"
                                            size="small"
                                            onClick={() => setIsFeedbackOpen(true)}
                                        >
                                            Xem chi tiết điểm & Đánh giá
                                        </Button>
                                    </div>
                                )}
                            </div>
                        </Card>
                    )}
                </div>
            )}

            <div className="mb-2">
                <Text strong>File bài làm:</Text>
                <div className="text-xs text-gray-500 mb-2">
                    Chấp nhận: {ALLOWED_EXTENSIONS.join(', ')} (tối đa 10MB)
                </div>
            </div>

            <Upload.Dragger {...handleUploadProps}>
                <p className="ant-upload-drag-icon">
                    <FileZipOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                </p>
                <p className="ant-upload-text">
                    Kéo thả file hoặc click để chọn file
                </p>
                <p className="ant-upload-hint">
                    {mySubmission?.link ? 'Upload file mới sẽ thay thế file cũ' : 'Chỉ hỗ trợ file nén (.zip, .rar, .7z, .tar.gz)'}
                </p>
            </Upload.Dragger>

            <FeedbackModal
                open={isFeedbackOpen}
                submission={mySubmission}
                onClose={() => setIsFeedbackOpen(false)}
            />
        </Modal>
    );
};
