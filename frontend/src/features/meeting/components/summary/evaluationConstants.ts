export const CRITERIA_LABEL_MAP: Record<string, string> = {
  // Trainer to Trainee / Meeting Overall
  ATTENDANCE_CONDUCT: 'Chuyên cần & Tác phong',
  INTERACTION_CONTRIBUTION: 'Mức độ Tương tác & Đóng góp',
  ABSORPTION_COMPREHENSION: 'Mức độ Tiếp thu & Hiểu bài',
  PRE_CLASS_PREPARATION: 'Mức độ Chuẩn bị bài trước buổi học',
  TRAINER_TO_TRAINEE_ATTENDANCE: 'Chuyên cần & Tác phong',
  TRAINER_TO_TRAINEE_INTERACTION: 'Mức độ Tương tác & Đóng góp',
  TRAINER_TO_TRAINEE_COMPREHENSION: 'Mức độ Tiếp thu & Hiểu bài',
  TRAINER_TO_TRAINEE_PREPARATION: 'Mức độ Chuẩn bị bài trước buổi học',
  // Trainee to Trainer
  CONTENT_QUALITY: 'Chất lượng Nội dung bài học',
  TEACHING_METHOD: 'Phương pháp Giảng dạy & Hỗ trợ',
  CLASS_ATMOSPHERE: 'Không khí Lớp học & Sự tương tác',
  PRACTICAL_VALUE: 'Giá trị Thu nhận & Tính ứng dụng',
  TRAINEE_TO_TRAINER_CONTENT: 'Chất lượng Nội dung bài học',
  TRAINEE_TO_TRAINER_METHOD: 'Phương pháp Giảng dạy & Hỗ trợ',
  TRAINEE_TO_TRAINER_ATMOSPHERE: 'Không khí Lớp học & Sự tương tác',
  TRAINEE_TO_TRAINER_VALUE: 'Giá trị Thu nhận & Tính ứng dụng',
};

export const TRAINER_TO_TRAINEE_CODES = new Set([
  'ATTENDANCE_CONDUCT',
  'INTERACTION_CONTRIBUTION',
  'ABSORPTION_COMPREHENSION',
  'PRE_CLASS_PREPARATION',
  'TRAINER_TO_TRAINEE_ATTENDANCE',
  'TRAINER_TO_TRAINEE_INTERACTION',
  'TRAINER_TO_TRAINEE_COMPREHENSION',
  'TRAINER_TO_TRAINEE_PREPARATION',
]);
