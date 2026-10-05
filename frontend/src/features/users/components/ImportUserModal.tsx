import { useState } from 'react';
import { DownloadOutlined, UploadOutlined } from '@ant-design/icons';
import { Alert, Button, message, Modal, Space, Typography, Upload } from 'antd';
import { useImportUsers } from '../hooks/useUsers';
import { userService } from '../services/user.service';
import type { UserImportResult } from '../types/user.types';

interface ImportUserModalProps {
    open: boolean;
    onCancel: () => void;
}

export const ImportUserModal = ({ open, onCancel }: ImportUserModalProps) => {
    const importUsers = useImportUsers();
    const [file, setFile] = useState<File | null>(null);
    const [result, setResult] = useState<UserImportResult | null>(null);
    const [downloadingTemplate, setDownloadingTemplate] = useState(false);

    const handleImport = async () => {
        if (!file) return;
        try {
            const res = await importUsers.mutateAsync(file);
            setResult(res.data);
            message.success('Import process completed');
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Import failed');
        }
    };

    const handleDownloadTemplate = async () => {
        try {
            setDownloadingTemplate(true);
            await userService.downloadTemplate();
            message.success('Tải file mẫu thành công');
        } catch {
            message.error('Không thể tải file mẫu. Vui lòng thử lại sau.');
        } finally {
            setDownloadingTemplate(false);
        }
    };

    const handleClose = () => {
        setFile(null);
        setResult(null);
        onCancel();
    };

    return (
        <Modal
            title={
                <Space>
                    <UploadOutlined /> Import Users from Excel
                </Space>
            }
            open={open}
            onCancel={handleClose}
            footer={[
                <Button key="close" onClick={handleClose}>
                    Close
                </Button>,
                !result && (
                    <Button
                        key="import"
                        type="primary"
                        onClick={handleImport}
                        disabled={!file}
                        loading={importUsers.isPending}
                    >
                        Import
                    </Button>
                ),
            ]}
            width={600}
        >
            {!result ? (
                <div className="py-4">
                    <Alert
                        message={
                            <div className="flex items-center justify-between">
                                <span>File Format Requirement</span>
                                <Button
                                    size="small"
                                    type="link"
                                    icon={<DownloadOutlined />}
                                    onClick={handleDownloadTemplate}
                                    loading={downloadingTemplate}
                                >
                                    Tải file mẫu (.xlsx)
                                </Button>
                            </div>
                        }
                        description={
                            <ul className="list-disc pl-4 mt-2">
                                <li>Format: .xlsx or .csv (UTF-8)</li>
                                <li>
                                    Required Columns: <b>name</b> (hoặc họ tên), <b>email</b>,{' '}
                                    <b>phone_number</b> (hoặc sđt)
                                </li>
                                <li>
                                    Default Role: <b>Teammate</b>
                                </li>
                            </ul>
                        }
                        type="info"
                        showIcon
                        className="mb-4"
                    />
                    <Upload.Dragger
                        beforeUpload={(file) => {
                            setFile(file);
                            return false;
                        }}
                        fileList={file ? [{ uid: '-1', name: file.name, status: 'done' }] : []}
                        onRemove={() => setFile(null)}
                        accept=".xlsx, .xls, .csv"
                        maxCount={1}
                    >
                        <p className="ant-upload-drag-icon">
                            <UploadOutlined className="text-4xl text-gray-400" />
                        </p>
                        <p className="ant-upload-text">Click or drag file to this area to upload</p>
                        <p className="ant-upload-hint">
                            Support for a single upload. Strictly prohibited from uploading company data or
                            other banned files.
                        </p>
                    </Upload.Dragger>
                </div>
            ) : (
                <div className="py-4 space-y-4">
                    <Alert
                        message="Import Completed"
                        description={`Total: ${result.total} | Success: ${result.success_count} | Error: ${result.error_count}`}
                        type={result.error_count > 0 ? 'warning' : 'success'}
                        showIcon
                    />

                    {result.errors && result.errors.length > 0 && (
                        <div className="max-h-60 overflow-y-auto border rounded p-2 bg-red-50">
                            <Typography.Text type="danger" strong>
                                Error Details:
                            </Typography.Text>
                            <ul className="list-disc pl-4 mt-1 text-sm text-red-600">
                                {result.errors.map((err: string) => (
                                    <li key={err}>{err}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </Modal>
    );
};
