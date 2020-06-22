import React from 'react';
import { Link } from 'react-router-dom'
import Drawer from '@material-ui/core/Drawer';
import AppBar from "@material-ui/core/AppBar";
import Toolbar from "@material-ui/core/Toolbar";
import List from '@material-ui/core/List';
import Hidden from '@material-ui/core/Hidden';
import Typography from '@material-ui/core/Typography';
import Divider from '@material-ui/core/Divider';
import ListItem from '@material-ui/core/ListItem';
import IconButton from '@material-ui/core/IconButton';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import AirPlayIcon from '@material-ui/icons/Airplay';
import MenuIcon from '@material-ui/icons/Menu';
import AccountBoxIcon from '@material-ui/icons/AccountBox';
import HelpIcon from '@material-ui/icons/Help';
import EmailIcon from '@material-ui/icons/Email';
import LibraryBooksIcon from '@material-ui/icons/LibraryBooks';
import Breadcrumbs from '@material-ui/core/Breadcrumbs';
import { makeStyles, useTheme } from '@material-ui/core/styles';

const drawerWidth = 240;

const useStyles = makeStyles(theme => ({
  root: {
    display: 'flex',
  },
  drawer: {
    [theme.breakpoints.up('sm')]: {
      width: drawerWidth,
      flexShrink: 0,
    },
  },
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
  },
  menuButton: {
    marginRight: theme.spacing(2),
    [theme.breakpoints.up('sm')]: {
      display: 'none',
    },
  },
  breadcrumbs: {
    marginBottom: 32,
  },
  drawerPaper: {
    width: drawerWidth,
  },
  toolbar: theme.mixins.toolbar,
  content: {
    flexGrow: 1,
    padding: theme.spacing(3),
    maxWidth: '100%',
    [theme.breakpoints.up('sm')]: {
      maxWidth: `calc(100% - ${drawerWidth}px)`,
    },
    [theme.breakpoints.up('md')]: {
      maxWidth: 960,
    },
    margin: '0 auto'
  },
}));

const Main = ({component: Component, props, breadcrumbs}) => {
  const classes = useStyles();
  const theme = useTheme();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <div>
      <div className={classes.toolbar} />
      <Divider />
      <List>
        <ListItem button component={Link} to="/sessions">
          <ListItemIcon><AirPlayIcon /></ListItemIcon>
          <ListItemText primary="Sessions" />
        </ListItem>
        <ListItem button component={Link} to="/simulations">
          <ListItemIcon><LibraryBooksIcon /></ListItemIcon>
          <ListItemText primary="Simulations" />
        </ListItem>
        <ListItem button component={Link} to="/account">
          <ListItemIcon><AccountBoxIcon /></ListItemIcon>
          <ListItemText primary="Account" />
        </ListItem>
      </List>
      <Divider />
      <List>
        <ListItem button component="a" href="https://gitlab.com" target="_blank" rel="noreferrer noopener">
          <ListItemIcon><HelpIcon /></ListItemIcon>
          <ListItemText primary="Help" />
        </ListItem>
        <ListItem button component="a" href="mailto:hello@narupa.xyz">
          <ListItemIcon><EmailIcon /></ListItemIcon>
          <ListItemText primary="Contact Us" />
        </ListItem>
      </List>
      <Divider />
    </div>
  );

  const container = window !== undefined ? () => window.document.body : undefined;


  return (
    <div className={classes.root}>
      <AppBar position="fixed" className={classes.appBar}>
        <Toolbar>
          <IconButton
              color="inherit"
              edge="start"
              onClick={handleDrawerToggle}
              className={classes.menuButton}
            >
              <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap>
            Napura Web
          </Typography>
        </Toolbar>
      </AppBar>
      <nav className={classes.drawer}>
        <Hidden smUp implementation="css">
          <Drawer
            container={container}
            variant="temporary"
            anchor={theme.direction === 'rtl' ? 'right' : 'left'}
            open={mobileOpen}
            onClose={handleDrawerToggle}
            classes={{
              paper: classes.drawerPaper,
            }}
            ModalProps={{
              keepMounted: true,
            }}
          >
            {drawer}
          </Drawer>
        </Hidden>
        <Hidden xsDown implementation="css">
          <Drawer
            classes={{
              paper: classes.drawerPaper,
            }}
            variant="permanent"
            open
          >
            {drawer}
          </Drawer>
        </Hidden>
      </nav>
      <main className={classes.content}>
        <Toolbar />
        {breadcrumbs &&
          <Breadcrumbs className={classes.breadcrumbs}>
            {breadcrumbs.map((breadcrumb, index) =>
              breadcrumb.path ?
                <Typography component={Link} variant='h4' color="inherit" to={breadcrumb.path} key={index}>
                  {breadcrumb.text}
                </Typography>
              : <Typography variant={breadcrumbs.length === 1 ? 'h4' : 'h6'} color="inherit" key={index}>
                  {breadcrumb.text}
                </Typography>
            )}
          </Breadcrumbs>
        }
        <Component {...props} />
      </main>
    </div>
  )
}

export default Main;