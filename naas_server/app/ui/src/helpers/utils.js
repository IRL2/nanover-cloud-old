import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

export const useInterval = (callback, delay) => {

  const savedCallback = useRef();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    function tick() {
      savedCallback.current();
    }
    if (delay !== null) {
      const id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}

export const useQuery = () => {
  return new URLSearchParams(useLocation().search);
}