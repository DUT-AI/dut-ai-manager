# Contract: Group Submissions By Exercise Function

## Function Signature
```typescript
export function groupSubmissionsByExercise(
  submissions: NormalizedSubmission[],
  allExercises?: ExerciseSummary[] | null
): ExerciseGroupSummary[];
```

## Contract Rules (Strict & No Fallback)
1. **Chỉ nhận CODING submissions**:
   - Nếu `submissions` có lẫn phần tử `submissionType === 'GAME'`, hàm phải tự động bỏ qua. Tuyệt đối không nhóm bản ghi Game vào mảng kết quả của bài tập coding con.
2. **Ưu tiên danh mục bài tập con gốc (`allExercises`)**:
   - Nếu `allExercises` được cung cấp ($M$ bài):
     - Mảng kết quả trả về đúng $M$ nhóm theo đúng thứ tự của `allExercises`.
     - Với mỗi bài tập con, nếu học viên chưa có bài nộp nào, kết quả trả về:
       ```typescript
       {
         exerciseId: ex.exercise_id,
         exerciseTitle: ex.title,
         submissions: [],
         attemptCount: 0,
         bestScore: null,
         latestSubmittedAt: '',
         isPassed: false
       }
       ```
3. **Cấm sinh nhóm fallback `__general__` ("Bài tập chung")**:
   - Bất kỳ bài nộp nào không có `exercise_id` (ví dụ bài nộp Game bị lọt vào) sẽ bị loại trừ, không sinh ra `exerciseTitle: 'Bài tập chung'`.
