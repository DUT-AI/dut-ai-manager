import React, { useState, useEffect, useRef } from 'react';
import { Input, type InputProps, type InputRef } from 'antd';

export interface CurrencyInputProps extends Omit<InputProps, 'value' | 'onChange'> {
  value?: number | null;
  onChange?: (value: number) => void;
  min?: number;
  max?: number;
}

function formatWithCommas(rawDigits: string): string {
  if (!rawDigits) return '';
  return rawDigits.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

export const CurrencyInput: React.FC<CurrencyInputProps> = ({
  value,
  onChange,
  onBlur,
  min = 0,
  max,
  ...restProps
}) => {
  const inputRef = useRef<InputRef>(null);

  const [displayValue, setDisplayValue] = useState<string>(() => {
    if (value === undefined || value === null) return '';
    return value.toLocaleString('en-US');
  });

  // Sync with external value changes (e.g. form.setFieldsValue or reset)
  useEffect(() => {
    if (value === undefined || value === null) {
      setDisplayValue('');
    } else {
      const currentDigits = displayValue.replace(/\D/g, '');
      const currentNum = currentDigits ? parseInt(currentDigits, 10) : 0;
      if (currentNum !== value) {
        setDisplayValue(value.toLocaleString('en-US'));
      }
    }
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target;
    const prevCursor = input.selectionStart || 0;
    const rawInput = input.value;
    const digitsBeforeCursor = rawInput.slice(0, prevCursor).replace(/\D/g, '').length;

    const rawDigits = rawInput.replace(/\D/g, '');

    // Check max if provided
    if (max !== undefined && rawDigits) {
      const parsed = parseInt(rawDigits, 10);
      if (parsed > max) return;
    }

    const formatted = formatWithCommas(rawDigits);

    // Calculate updated cursor position based on digits before cursor
    let newCursor = 0;
    let digitsSeen = 0;
    for (let i = 0; i < formatted.length; i++) {
      if (/\d/.test(formatted[i])) {
        digitsSeen++;
      }
      newCursor = i + 1;
      if (digitsSeen >= digitsBeforeCursor) {
        break;
      }
    }
    if (digitsBeforeCursor === 0) newCursor = 0;

    setDisplayValue(formatted);

    const numValue = rawDigits ? parseInt(rawDigits, 10) : min;
    onChange?.(numValue);

    requestAnimationFrame(() => {
      const nativeInput = inputRef.current?.input;
      if (nativeInput) {
        nativeInput.setSelectionRange(newCursor, newCursor);
      }
    });
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const rawDigits = displayValue.replace(/\D/g, '');
    if (!rawDigits) {
      setDisplayValue('');
      onChange?.(min);
    } else {
      let num = parseInt(rawDigits, 10);
      if (min !== undefined && num < min) num = min;
      if (max !== undefined && num > max) num = max;
      setDisplayValue(num.toLocaleString('en-US'));
      onChange?.(num);
    }
    onBlur?.(e);
  };

  return (
    <Input
      ref={inputRef}
      value={displayValue}
      onChange={handleChange}
      onBlur={handleBlur}
      inputMode="numeric"
      {...restProps}
    />
  );
};

export default CurrencyInput;
