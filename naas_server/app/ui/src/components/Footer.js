import React from 'react';
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles(theme => ({
  root: {
    position: 'absolute',
    bottom: 0,
    padding: 16,
    fontSize: 11,
  },
  link: {
    color: '#ff6600'
  },
}));

const Footer = () => {
  const classes = useStyles();
  
  return (
    <div className={classes.root}>
      <span>Website design is (c) 2020 </span>
      <a 
        href="https://www.artsci.international/"
        className={classes.link}
        target="_blank"
        rel="noopener noreferrer">
          ArtSci International
      </a>
      <span> Foundation, distributed under </span>
      <a 
        href="https://creativecommons.org/licenses/by-sa/4.0/legalcode"
        className={classes.link}
        target="_blank"
        rel="noopener noreferrer">
          CC-SA 4.0
      </a>
    </div>
  )
}

export default Footer;