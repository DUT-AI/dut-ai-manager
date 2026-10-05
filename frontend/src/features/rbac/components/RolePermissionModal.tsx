import { useEffect, useState } from 'react';
import { Checkbox, Grid, List, message, Modal, Spin, Transfer, Typography } from 'antd';
import type { TransferProps } from 'antd';
import {
    useAddPermissionToRole,
    usePermissions,
    useRemovePermissionFromRole,
    useRole,
} from '../hooks/useRbac';

const { Text } = Typography;

interface RolePermissionModalProps {
    open: boolean;
    roleId: number | null;
    roleName?: string;
    onClose: () => void;
}

export const RolePermissionModal = ({
    open,
    roleId,
    roleName,
    onClose,
}: RolePermissionModalProps) => {
    const screens = Grid.useBreakpoint();

    // Lazy load role with permissions only when modal is open
    const { data: roleDetail, isLoading: roleLoading } = useRole(roleId, open);
    const { data: permissions = [], isLoading: permsLoading } = usePermissions(open);

    const addPermissionToRole = useAddPermissionToRole();
    const removePermissionFromRole = useRemovePermissionFromRole();

    const [targetKeys, setTargetKeys] = useState<string[]>([]);
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        if (open && roleDetail?.permissions) {
            setTargetKeys(roleDetail.permissions.map((p) => p.id.toString()));
        } else if (!open) {
            setTargetKeys([]);
        }
    }, [open, roleDetail]);

    const handlePermTransfer: TransferProps['onChange'] = async (
        nextTargetKeys,
        direction,
        moveKeys
    ) => {
        if (!roleId) return;

        try {
            setActionLoading(true);
            for (const key of moveKeys) {
                const permId = parseInt(key as string);
                if (direction === 'right') {
                    await addPermissionToRole.mutateAsync({ roleId, permId });
                } else {
                    await removePermissionFromRole.mutateAsync({ roleId, permId });
                }
            }
            message.success('Permissions updated successfully');
            setTargetKeys(nextTargetKeys as string[]);
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Failed to update permissions');
        } finally {
            setActionLoading(false);
        }
    };

    const handleMobilePermToggle = async (permId: number, checked: boolean) => {
        if (!roleId) return;
        try {
            setActionLoading(true);
            if (checked) {
                await addPermissionToRole.mutateAsync({ roleId, permId });
            } else {
                await removePermissionFromRole.mutateAsync({ roleId, permId });
            }
            const newKeys = checked
                ? [...targetKeys, permId.toString()]
                : targetKeys.filter((k) => k !== permId.toString());
            setTargetKeys(newKeys);
            message.success('Permission updated successfully');
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Failed to update permission');
        } finally {
            setActionLoading(false);
        }
    };

    const isOverallLoading = roleLoading || permsLoading || actionLoading;

    return (
        <Modal
            title={`Permissions: ${(roleName || roleDetail?.name || '').toUpperCase()}`}
            open={open}
            onCancel={onClose}
            width={screens.md ? 700 : '95%'}
            footer={null}
            centered
            destroyOnHidden
            styles={{
                body: {
                    maxHeight: '70vh',
                    overflowY: 'auto',
                    padding: screens.md ? '24px' : '12px',
                },
            }}
        >
            <Spin spinning={isOverallLoading}>
                <div className="mt-2">
                    {screens.md ? (
                        <div className="flex justify-center">
                            <Transfer
                                dataSource={permissions.map((p) => ({
                                    key: p.id.toString(),
                                    title: `${p.resource}:${p.action}`,
                                    description: p.description || '',
                                }))}
                                titles={['Available', 'Assigned']}
                                targetKeys={targetKeys}
                                onChange={handlePermTransfer}
                                render={(item) => item.title}
                                disabled={actionLoading}
                                listStyle={{
                                    width: 300,
                                    height: 400,
                                }}
                            />
                        </div>
                    ) : (
                        <List
                            dataSource={permissions}
                            renderItem={(p) => (
                                <List.Item className="!px-0">
                                    <Checkbox
                                        checked={targetKeys.includes(p.id.toString())}
                                        onChange={(e) => handleMobilePermToggle(p.id, e.target.checked)}
                                        className="w-full"
                                        disabled={actionLoading}
                                    >
                                        <div className="flex flex-col ml-2">
                                            <Text strong>
                                                {p.resource}:{p.action}
                                            </Text>
                                            {p.description && (
                                                <Text type="secondary" className="text-xs">
                                                    {p.description}
                                                </Text>
                                            )}
                                        </div>
                                    </Checkbox>
                                </List.Item>
                            )}
                        />
                    )}
                </div>
            </Spin>
        </Modal>
    );
};
