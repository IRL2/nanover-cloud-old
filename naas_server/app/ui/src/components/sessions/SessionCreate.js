import React, { useState, useEffect} from "react";
import { useHistory, useParams } from "react-router-dom";
import { makeStyles } from '@material-ui/core/styles';
import { getSimulations, createSession, updateSession, getSession } from '../../helpers/api';
import { getSupportedTimezones } from '../../helpers/timezones';
import moment from 'moment-timezone';
import Button from "@material-ui/core/Button";
import TextField from '@material-ui/core/TextField';
import FormControl from '@material-ui/core/FormControl';
import InputLabel from '@material-ui/core/InputLabel';
import Select from '@material-ui/core/Select';
import CircularProgress from '@material-ui/core/CircularProgress';
import Checkbox from '@material-ui/core/Checkbox';
import FormControlLabel from '@material-ui/core/FormControlLabel';

const useStyles = makeStyles((theme) => ({
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
    justifyContent: 'space-evenly',
    [theme.breakpoints.down('md')]: {
      flexFlow: 'column',
      marginBottom: 16
    }
  },
  formDate: {
    flexGrow: 1,
    marginRight: 16,
    marginBottom: 16,
    [theme.breakpoints.down('md')]: {
      marginRight: 0
    }
  },
  submit: {
    marginBottom: 8
  }
}));

const DATE_FORMAT = 'YYYY-MM-DDTHH:mm:ss';

const SessionCreate = () => {
  const defaultStartAt = moment().startOf('hour').add(1, 'hour');
  const classes = useStyles();
  const { sessionId } = useParams();
  const history = useHistory();
  const [session, setSession] = useState({
    start_at: defaultStartAt.format(DATE_FORMAT),
    end_at: defaultStartAt.add(1, 'hours').format(DATE_FORMAT),
    timezone: moment.tz.guess(true),
    branch: 'master',
    location: 'Frankfurt',
    record: false,
    simulation: {},
    //create_conference: true
    create_conference: false
  });
  const [loading, setLoading] = useState(true);
  const [simulationList, setSimulationList] = useState([]);
  const [submitting, setSubmitting] = useState(false);

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
            return {...s, simulation: { id: result.items[0].id }}
          });
        }
      } catch (e) {
        console.log(e);
      }
      setLoading(false);
    })();
  }, [sessionId]);

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
    setSession({...session, start_at: appendSeconds(e.currentTarget.value)});
  }

  const onChangeEndAt = e => {
    setSession({...session, end_at: appendSeconds(e.currentTarget.value)});
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
      setSubmitting(false)
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
        <FormControl variant="outlined" className={classes.formControl}>
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
          label="Description (optional)"
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
          />
          <TextField
            label="End at"
            type="datetime-local"
            variant="outlined"
            defaultValue={session.end_at}
            onChange={onChangeEndAt}
            className={classes.formDate}
            inputProps={{ 
              'min': session.start_at,
              'max': moment(session.start_at).add(2, 'hours').format(DATE_FORMAT)
            }}
          />
          <FormControl variant="outlined">
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
        <FormControl variant="outlined" className={classes.formControl}>
          <InputLabel>Server location</InputLabel>
          <Select
            native
            defaultValue={session.location}
            onChange={onChangeLocation}
            label="Server location"
          >
            <option value='Frankfurt'>Frankfurt</option>
            <option value='London'>London</option>
            <option value='Ashburn'>Washington, D.C.</option>
          </Select>
        </FormControl>
        <TextField
          variant="outlined"
          label="Branch"
          defaultValue={session.branch}
          onChange={onChangeBranch}
          className={classes.formControl}
        />
	{/*
        <FormControlLabel variant="outlined" className={classes.formControl}
          control={
            <Checkbox
              defaultChecked={session.record}
              onChange={onChangeRecord}
              color="primary"
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
    </div>
  )
}

export default SessionCreate;
