import { useState } from "react";

const useToggle = (initialState: boolean) => {
    const [value, setValue] = useState<boolean>(initialState);
    const toggle = (newValue?: boolean) => setValue(newValue ?? !value);
    return [value, toggle] as const;
};

export default useToggle;