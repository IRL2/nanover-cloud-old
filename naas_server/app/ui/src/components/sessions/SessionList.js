import React, { useState, useEffect } from "react";
import { makeStyles } from '@material-ui/core/styles';
import { getSessions, deleteSession, deleteInstance } from '../../helpers/api';
import { useInterval } from '../../helpers/utils';
import _ from 'lodash';
import moment from 'moment-timezone';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import { Link } from 'react-router-dom'
import AppBar from '@material-ui/core/AppBar';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import Button from "@material-ui/core/Button";
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';
import IconButton from '@material-ui/core/IconButton';
import DeleteIcon from '@material-ui/icons/Delete';
import EditIcon from '@material-ui/icons/Edit';
import CancelIcon from '@material-ui/icons/Cancel';
import FileCopyIcon from '@material-ui/icons/FileCopy';
import Dialog from '@material-ui/core/Dialog';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogActions from '@material-ui/core/DialogActions';
import DialogTitle from '@material-ui/core/DialogTitle';
import CircularProgress from '@material-ui/core/CircularProgress';
import Typography from "@material-ui/core/Typography";
import Tooltip from "@material-ui/core/Tooltip";

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  },
  appBar: {
    backgroundColor: theme.palette.background.paper,
    color: '#000',
    marginBottom: 16
  },
  scheduleSessionBtn: {
    marginBottom: 32
  },
  link: {
    color: '#ff6600'
  },
  simulationImage: {
    maxWidth: 400,
    maxHeight: 400,
    marginBottom: 8
  },
  sessionRow: {
    height: 80
  },
  tdTime: {
    minWidth: 175
  },
  tdActions: {
    minWidth: 130
  },
  tdNarupaIcon: {
    fontSize: 14
  },
  copyableLink: {
    display: 'flex',
    alignItems: 'center'
  },
  copyableLinkIcon: {
    fontSize: 14,
  }
}));

function TabPanel({ children, value, index }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
    >
      {value === index && (
        <div>{children}</div>
      )}
    </div>
  );
}

function CopyableLink({ url, display }) {
  const classes = useStyles();

  return (
    <div className={classes.copyableLink}>
      <a 
        href={url}
        className={classes.link}
        target="_blank"
        rel="noopener noreferrer"
      >
        <Typography>{display}</Typography>
      </a>
      <CopyToClipboard 
        text={url}
      >
        <Tooltip title="Copy">
          <IconButton>
            <FileCopyIcon className={classes.copyableLinkIcon}/>
          </IconButton>
        </Tooltip>
      </CopyToClipboard>
    </div>
  )
}

function FormattedSessionDate({ session }) {
  const startAt = moment(session.start_at).format('DD MMM HH:mm');
  const endAt = moment(session.end_at).format('HH:mm');
  const timezoneAbbr = moment.tz(session.timezone).zoneAbbr();
  const timezoneOffset = moment.tz(session.timezone).format('ZZ');
  return (
    <div>
      <Typography>{startAt}-{endAt}</Typography>
      <Typography variant="body2">{timezoneAbbr}{timezoneOffset} {session.timezone}</Typography>
    </div>
  )
}


const SessionList = () => {
  const classes = useStyles();
  const [loading, setLoading] = useState(true);
  const [sessionList, setSessionList] = useState([]);
  const [deletingSession, setDeletingSession] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [stoppingSession, setStoppingSession] = useState(null);
  const [stopping, setStopping] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [simulationDialog, setSimulationDialog] = useState(null);

  const refreshSessionList = async () => {
    try {
      const result = await getSessions();
      setSessionList(result.items);
    } catch (e) {
      console.log(e);
    }
  }

  useEffect(() => {
    (async () => {
      refreshSessionList();
      setLoading(false);
    })();
  }, []);

  useInterval(refreshSessionList, 30 * 1000);

  const handleDeleteDialogOpen = session => setDeletingSession(session);

  const handleDeleteDialogClose = async (confirm) => {
    setDeleting(true);
    if (confirm) {
      try {
        await deleteSession(deletingSession.id);
        const result = await getSessions();
        setSessionList(result.items);
      } catch (e) {
        console.log(e);
      }
    }
    setDeleting(false);
    setDeletingSession(null);
  };

  const handleStopDialogOpen = session => setStoppingSession(session);

  const handleStopDialogClose = async (confirm) => {
    setStopping(true);
    if (confirm) {
      try {
        await deleteInstance(stoppingSession.id);
        const result = await getSessions();
        setSessionList(result.items);
      } catch (e) {
        console.log(e);
      }
    }
    setStopping(false);
    setStoppingSession(null);
  };

  const handleChangeTab = (e, newValue) => setTabValue(newValue);

  const handleSimulationDialogClose = () => setSimulationDialog(null);

  const onClickSimulation = (simulation) => setSimulationDialog(simulation);

  const getNarupaContent = session => {
    const instance = session.instance;
    if (instance) {
      if (instance.status === 'PENDING') {
        return 'Pending';
      } else if (instance.status === 'WARMING') {
        return 'Warming up';
      } else if (instance.status === 'STOPPED') {
        return 'Stopped';
      } else if (instance.status === 'LAUNCHED') {
        return <CopyableLink url={`${instance.ip}`} display={instance.ip}/>
      } else {
        return 'Unknown';
      }
    }
  }

  const [previousSessions, upcomingSessions] = _.partition(sessionList || [], (s) => moment(s.end_at).isBefore(moment()));
  
  return (
    loading ?
    <CircularProgress/>
    :
    <div className={classes.root}>
      <Button
        color="primary"
        variant="contained"
        className={classes.scheduleSessionBtn}
        component={Link}
        to="/sessions/create"
      >
        Schedule a session
      </Button>
      <AppBar position="static" className={classes.appBar}>
        <Tabs value={tabValue} onChange={handleChangeTab}>
          <Tab label="Upcoming Sessions"/>
          <Tab label="Previous Sessions"/>
        </Tabs>
      </AppBar>
      <TabPanel value={tabValue} index={0}>
        <TableContainer component={Paper}>
          <Table className={classes.table}>
            <TableHead>
              <TableRow>
                <TableCell>Time</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Simulation</TableCell>
	  	{/*
                <TableCell>Conference</TableCell>
		*/}
                <TableCell>Narupa</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {upcomingSessions.map((session) => (
                <TableRow key={session.id} className={classes.sessionRow}>
                  <TableCell className={classes.tdTime}>
                    <FormattedSessionDate session={session} />
                  </TableCell>
                  <TableCell>
                    <Typography>{session.description}</Typography>
                  </TableCell>
                  <TableCell>
                    <Button
                      onClick={() => onClickSimulation(session.simulation)}
                      className={classes.link}
                    >
                      <Typography>{session.simulation.name}</Typography>
                    </Button>
                  </TableCell>
		  {/*
                  <TableCell>
                    {session.zoom_meeting ?
                      <CopyableLink
                        url={session.zoom_meeting.join_url}
                        display="Zoom"
                      />
                    : ''}
                  </TableCell>
		  */}
                  <TableCell>
                    {getNarupaContent(session)}
                  </TableCell>
                  <TableCell className={classes.tdActions}>
                    {session.instance.status === 'PENDING' && 
                      <>
                        <Tooltip title="Edit">
                          <IconButton component={Link} to={`/sessions/${session.id}`} >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton onClick={() => handleDeleteDialogOpen(session)} >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </>
                    }
                    {(session.instance.status === 'LAUNCHED' || session.instance.status === 'WARMING') && 
                      <Tooltip title="Stop">
                        <IconButton onClick={() => handleStopDialogOpen(session)}>
                          <CancelIcon />
                        </IconButton>
                      </Tooltip>
                    }
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        <TableContainer component={Paper}>
          <Table className={classes.table}>
            <TableHead>
              <TableRow>
                <TableCell>Time</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Simulation</TableCell>
                <TableCell>Recording</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {previousSessions.map((session) => (
                <TableRow key={session.id} className={classes.sessionRow}>
                  <TableCell className={classes.tdTime}>
                    <FormattedSessionDate session={session} />
                  </TableCell>
                  <TableCell>
                    <Typography>{session.description}</Typography>
                  </TableCell>
                  <TableCell>
                    <Button
                      href="#" 
                      onClick={() => onClickSimulation(session.simulation)}
                      className={classes.link}
                    >
                      <Typography>{session.simulation.name}</Typography>
                    </Button>
                  </TableCell>
                  <TableCell>
                    <Typography>{session.recording}</Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>
      <Dialog
        open={deletingSession != null}
        onClose={() => handleDeleteDialogClose(false)}
      >
        <DialogTitle>Are you sure you want to delete this session?</DialogTitle>
        <DialogActions>
          <Button onClick={() => handleDeleteDialogClose(false)} color="secondary" disabled={deleting}>
            Cancel
          </Button>
          <Button onClick={() => handleDeleteDialogClose(true)} color="primary" autoFocus disabled={deleting}>
            Yes
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog
        open={stoppingSession != null}
        onClose={() => handleStopDialogClose(false)}
      >
        <DialogTitle>Are you sure you want to stop Narupa?</DialogTitle>
        <DialogActions>
          <Button onClick={() => handleStopDialogClose(false)} color="secondary" disabled={stopping}>
            Cancel
          </Button>
          <Button onClick={() => handleStopDialogClose(true)} color="primary" autoFocus disabled={stopping}>
            Yes
          </Button>
        </DialogActions>
      </Dialog>
      {simulationDialog &&
        <Dialog
          open={simulationDialog != null}
          onClose={handleSimulationDialogClose}
        >
          <DialogTitle>{simulationDialog.name}</DialogTitle>
          <DialogContent>
            <img 
              src={simulationDialog.image_url} 
              className={classes.simulationImage}
              alt={simulationDialog.name}
            />
            <DialogContentText>
                {simulationDialog.filename}
            </DialogContentText>
            <DialogContentText>
                {simulationDialog.description}
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleSimulationDialogClose} color="primary" autoFocus>
              OK
            </Button>
          </DialogActions>
        </Dialog>
      }
    </div>
  )
}

export default SessionList;
