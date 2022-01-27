import React, { useState, useEffect} from "react";
import { useHistory, useParams } from "react-router-dom";
import { makeStyles } from '@material-ui/core/styles';
import { getSimulations, createSession, updateSession, getSession } from '../../helpers/api';
import { getSupportedTimezones } from '../../helpers/timezones';
import { useQuery } from '../../helpers/utils';
import { getGcpLocations } from '../../helpers/gcp';
import _ from 'lodash';
import moment from 'moment-timezone';
import Button from "@material-ui/core/Button";
import TextField from '@material-ui/core/TextField';
import FormControl from '@material-ui/core/FormControl';
import InputLabel from '@material-ui/core/InputLabel';
import Select from '@material-ui/core/Select';
import CircularProgress from '@material-ui/core/CircularProgress';
import Checkbox from '@material-ui/core/Checkbox';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Snackbar from '@material-ui/core/Snackbar';
import Alert from '@material-ui/lab/Alert';

const useStyles = makeStyles(theme => ({
  root: {
    flexGrow: 1
  },
  form: {
    display: 'flex',
    flexFlow: 'column'
  },
  formControl: {
    marginBottom: 16
  },
  formSelect: {
    paddingTop: 16
  },
  formDates: {
    display: 'flex',
    [theme.breakpoints.down('sm')]: {
      flexFlow: 'column',
      marginBottom: 16
    }
  },
  formDate: {
    marginRight: 16,
    marginBottom: 16,
    minWidth: 305,
    [theme.breakpoints.down('sm')]: {
      marginRight: 0
    }
  },
  submit: {
    marginBottom: 8
  }
}));

const DATE_FORMAT = 'YYYY-MM-DDTHH:mm:ss';
const MAX_DURATION = 5 * 60;
const DEFAULT_DURATION = 60;

const SessionCreate = () => {
  const defaultStartAt = moment().startOf('minute');
  const simulationId = useQuery().get('simulationId');
  const gcpLocations = _.groupBy(getGcpLocations(), 'group');
  const classes = useStyles();
  const { sessionId } = useParams();
  const history = useHistory();
  const [session, setSession] = useState({
    start_at: defaultStartAt.format(DATE_FORMAT),
    end_at: defaultStartAt.add(DEFAULT_DURATION, 'minutes').format(DATE_FORMAT),
    timezone: moment.tz.guess(true),
    branch: 'master',
    location: 'europe-west2',
    record: false,
    simulation: {},
    create_conference: false
  });
  const [duration, setDuration] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simulationList, setSimulationList] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const result = await getSimulations();
        setSimulationList(result.items);

        if (sessionId) {
          const sessionResult = await getSession(sessionId);
          setSession(sessionResult);
        } else if (result.items.length > 0) {
          setSession(s => {
            return {...s, simulation: { id: simulationId || result.items[0].id }}
          });
        }
      } catch (e) {
        console.log(e);
      }
      setLoading(false);
    })();
  }, [sessionId, simulationId]);

  useEffect(() => {
    const diff = moment.duration(moment(session.end_at).diff(moment(session.start_at)));
    if (diff.asMinutes() > 0) {
      setDuration(diff.asMinutes());
    }
  }, [session]);

  const onChangeBranch = e => {
    setSession({...session, branch: e.currentTarget.value});
  }

  const onChangeDescription = e => {
    setSession({...session, description: e.currentTarget.value});
  }

  const onChangeLocation = e => {
    setSession({...session, location: e.currentTarget.value});
  }

  const onChangeTimezone = e => {
    const select = e.currentTarget;
    setSession({...session, timezone: select.options[select.selectedIndex].value});
  }

  const onChangeSimulation = e => {
    const select = e.currentTarget;
    session.simulation.id = select.options[select.selectedIndex].value
  }

  const appendSeconds = t => t.length === 16 ? t + ':00' : t

  const onChangeStartAt = e => {
    const startAt = appendSeconds(e.currentTarget.value);
    const endAt = moment(startAt).add(duration, 'minutes').format(DATE_FORMAT);
    setSession({...session, end_at: endAt, start_at: startAt});
  }

  const onChangeDuration = e => {
    setDuration(e.currentTarget.value);
    const endAt = moment(session.start_at).add(e.currentTarget.value, 'minutes').format(DATE_FORMAT);
    setSession({...session, end_at: endAt});
  }

  const onChangeRecord = e => {
    setSession({...session, record: e.currentTarget.checked});
  }

  const onChangeCreateConference = e => {
    setSession({...session, create_conference: e.currentTarget.checked});
  }

  const onSubmit = async e => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (sessionId) {
        await updateSession(session);
      } else {
        await createSession(session);
      }
      history.push('/sessions');
    } catch (e) {
      console.log(e);
      setSubmitting(false);
      setSnackbarMessage(e.response.data.message);
    }
  }

  const onCancel = () => {
    history.push('/sessions');
  };

  return (
    loading ?
    <CircularProgress/>
    :
    <div className={classes.root}>
      <form noValidate className={classes.form}>
        <FormControl variant="outlined" className={classes.formControl} required>
          <InputLabel>Simulation</InputLabel>
          <Select
            native
            defaultValue={session.simulation.id}
            onChange={onChangeSimulation}
            label="Simulation"
            disabled={!!sessionId}
          >
            {simulationList.map((simulation) => 
              <option value={simulation.id} key={simulation.id}>{simulation.name}</option>
            )}
          </Select>
        </FormControl>
        <TextField
          variant="outlined"
          label="Description"
          defaultValue={session.description}
          onChange={onChangeDescription}
          className={classes.formControl}
        />
        <div className={classes.formDates}>
          <TextField
            label="Start at"
            type="datetime-local"
            variant="outlined"
            defaultValue={session.start_at}
            onChange={onChangeStartAt}
            className={classes.formDate}
            inputProps={{ 
              'min': defaultStartAt.format(DATE_FORMAT)
            }}
            required
          />
          <FormControl variant="outlined" className={classes.formDate} required>
            <InputLabel>Duration</InputLabel>
            <Select
              native
              defaultValue={duration}
              onChange={onChangeDuration}
              label="Duration"
            >
              {_.range(15, MAX_DURATION + 15, 15).map(i =>
                <option key={i} value={i}>{`${Math.floor(i / 60)}h ${i % 60}m`}</option>
              )}
            </Select>
          </FormControl>
          <FormControl variant="outlined" required>
            <InputLabel>Timezone</InputLabel>
            <Select
              native
              defaultValue={session.timezone}
              onChange={onChangeTimezone}
              label="Timezone"
            >
              {getSupportedTimezones().map(tz =>
                <option value={tz} key={tz}>
                  {`${tz} (${moment.tz(tz).zoneAbbr()} ${moment.tz(tz).format('ZZ')})`}
                </option>
              )}
            </Select>
          </FormControl>
        </div>
        <FormControl variant="outlined" className={classes.formControl} required>
          <InputLabel>Server location</InputLabel>
          <Select
            native
            defaultValue={session.location}
            onChange={onChangeLocation}
            label="Server location"
          >
            {Object.keys(gcpLocations).map(group =>
                <optgroup label={group} key={group}>
                  {gcpLocations[group].map(location =>
                    <option key={location.region} value={location.region}>{location.display}</option>
                  )}
                </optgroup>
            )}
          </Select>
        </FormControl>
        <TextField
          variant="outlined"
          label="Branch"
          defaultValue={session.branch}
          onChange={onChangeBranch}
          className={classes.formControl}
          required
        />
	{/*
        <FormControlLabel variant="outlined" className={classes.formControl}
          control={
            <Checkbox
              defaultChecked={session.record}
              onChange={onChangeRecord}
              color="primary"
              disabled
            />
          }
          label="Record session"
        />
	*/}
	{/*
        {!sessionId && 
          <FormControlLabel variant="outlined" className={classes.formControl}
            control={
              <Checkbox
                defaultChecked={session.create_conference}
                onChange={onChangeCreateConference}
                color="primary"
                disabled
              />
            }
            label="Create Zoom meeting"
          />
        }
	*/}
        <Button 
          type="submit"
          color="primary"
          variant="contained"
          onClick={onSubmit}
          className={classes.submit}
          disabled={submitting}
        >
          {sessionId ? 'Save' : 'Schedule'}
        </Button>
        <Button 
          variant="outlined"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </Button>
      </form> 
      <Snackbar 
        open={!!snackbarMessage} 
        autoHideDuration={6000} 
        onClose={() => setSnackbarMessage(null)} 
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
          <Alert 
            onClose={() => setSnackbarMessage(null)} 
            severity="error">
              {snackbarMessage}
          </Alert>
      </Snackbar>
    </div>
  )
}

export default SessionCreate;
