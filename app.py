from pathlib import Path
import math,json,textwrap
import pandas as pd,numpy as np,streamlit as st,plotly.graph_objects as go,plotly.express as px
P=Path(__file__).parent/'data';need=['locations.csv','dimensions.csv','quality_report.csv','relationships.csv'];missing=[x for x in need if not (P/x).exists()]
if missing:st.error('V7.2 needs the V7 data folder. Missing: '+', '.join(missing));st.stop()
L=pd.read_csv(P/'locations.csv');D=pd.read_csv(P/'dimensions.csv');Q=pd.read_csv(P/'quality_report.csv');K=D.dimension_key.tolist();LAB=dict(zip(D.dimension_key,D.label))
THEMES={'Home & value':['housing_cost','housing_choice'],'Everyday life':['daily_services','healthcare','digital'],'Connections':['rail','road','airport','family_network'],'Outdoors':['walking','greenspace','waterside','climate','terrain'],'Culture & community':['food','culture','learning','community'],'Character & future':['heritage','independence','pace','safety','future_fit']}
PRESETS={'Stephen & Julie':{'household':'Retired couple','budget':'£1m–£2m','horizon':'3–8 years','notes':'Restaurants, walking, culture, travel and staying close to family. Character without isolation.','weights':{'Home & value':6,'Everyday life':8,'Connections':10,'Outdoors':9,'Culture & community':9,'Character & future':8}},'Active coastal next chapter':{'household':'Retired couple','budget':'£750k–£1m','horizon':'0–3 years','notes':'Coast, walking, community and year-round life matter most.','weights':{'Home & value':6,'Everyday life':7,'Connections':6,'Outdoors':10,'Culture & community':8,'Character & future':9}}}
st.set_page_config(page_title='Location Lifestyle AI V7.2',page_icon='🧭',layout='wide');st.markdown('''<style>.block-container{padding-top:1rem}.hero{padding:1.15rem 1.5rem;border-radius:18px;background:linear-gradient(120deg,#10372b,#527c67);color:white}.brief{padding:.9rem 1.1rem;border-left:6px solid #dba641;background:#f7faf8;border-radius:12px}.stTabs [data-baseweb="tab"]{font-size:.91rem}</style>''',unsafe_allow_html=True)
if 'profile' not in st.session_state:st.session_state.profile=PRESETS['Stephen & Julie'].copy()
if 'network' not in st.session_state:st.session_state.network=pd.DataFrame([{'Remove':False,'Place':'St Albans','Category':'Family','Importance':10,'Visits/month':4.0},{'Remove':False,'Place':'Marlow','Category':'Home / friends','Importance':7,'Visits/month':2.0}])
if 'floor' not in st.session_state:st.session_state.floor=58
ROAD_MPH,ROAD_OVER=35,10;PT_MPH,PT_OVER=45,30
def miles(a,b,c,d):
 z=math.sin(math.radians(c-a)/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(math.radians(d-b)/2)**2;return 7917.6*math.asin(math.sqrt(z))
def mins(mi,mode):return (ROAD_OVER+60*mi/ROAD_MPH) if mode=='Road' else (PT_OVER+60*mi/PT_MPH)
def journeys(r,score_mode='Road'):
 rows=[]
 for _,n in st.session_state.network.iterrows():
  h=L[L.name==n.Place]
  if h.empty:continue
  mi=miles(r.latitude,r.longitude,h.iloc[0].latitude,h.iloc[0].longitude);road=mins(mi,'Road');pt=mins(mi,'Public transport');chosen=road if score_mode=='Road' else pt;vis=float(n['Visits/month']);rows.append({'Place':n.Place,'Category':n.Category,'Importance':float(n.Importance),'Visits/month':vis,'Miles':mi,'Road minutes':road,'Public transport minutes':pt,'Road monthly hours':2*road*vis/60,'Public transport monthly hours':2*pt*vis/60,'Node score':max(0,100-chosen/3),'lat':h.iloc[0].latitude,'lon':h.iloc[0].longitude})
 return pd.DataFrame(rows)
def nscore(r):
 z=journeys(r,'Road');return 75 if z.empty else float(np.average(z['Node score'],weights=z.Importance*np.maximum(z['Visits/month'],.25)))
def scoring():
 ww={k:st.session_state.profile['weights'][t] for t,ks in THEMES.items() for k in ks};w=np.array([ww[k] for k in K]);o=L.copy();o['Lifestyle']=o[K].to_numpy()@w/(10*w.sum())*100;o['Life Network']=o.apply(nscore,axis=1);o['Balanced']=.55*o.Lifestyle+.45*o['Life Network'];return o.sort_values(['Balanced','importance_rank'],ascending=[False,True]),ww
def gauge(v,title,key):
 title='<br>'.join(textwrap.wrap(title,15));f=go.Figure(go.Indicator(mode='gauge+number',value=v,title={'text':title,'font':{'size':11}},number={'font':{'size':21}},gauge={'axis':{'range':[0,100],'tickfont':{'size':7}},'bar':{'color':'#2d6a51'},'steps':[{'range':[0,45],'color':'#f2d0c9'},{'range':[45,70],'color':'#f1dfae'},{'range':[70,100],'color':'#acd1bd'}]}));f.update_layout(height=138,margin=dict(l=7,r=7,t=38,b=2));st.plotly_chart(f,use_container_width=True,key=key)
def hhmm(m):
 h=int(m//60);mm=int(round(m%60));return f'{h}h {mm:02d}m' if h else f'{mm}m'
def journey_map(candidate,z,view):
 f=go.Figure();times='Road minutes' if view=='Road' else 'Public transport minutes';burden='Road monthly hours' if view=='Road' else 'Public transport monthly hours'
 for _,n in z.iterrows():
  m=n[times];colour='#27935a' if m<=60 else '#d99c2f' if m<=120 else '#c74840';label=f"{n.Place}<br>{n.Miles:.0f} miles<br>{view}: {hhmm(m)}<br>{n[burden]:.1f} h/month"
  f.add_trace(go.Scattergeo(lon=[candidate.longitude,n.lon],lat=[candidate.latitude,n.lat],mode='lines',line=dict(color=colour,width=2+3*n.Importance/10),hoverinfo='text',text=[label,label],showlegend=False));f.add_trace(go.Scattergeo(lon=[n.lon],lat=[n.lat],mode='markers+text',text=[n.Place],textposition='top center',marker=dict(size=9+n.Importance,color=colour,line=dict(width=1,color='white')),hovertext=label,hoverinfo='text',name=n.Place))
 f.add_trace(go.Scattergeo(lon=[candidate.longitude],lat=[candidate.latitude],mode='markers+text',text=[candidate['name']],textposition='top center',marker=dict(size=25,color='#153d31',symbol='star',line=dict(width=1,color='white')),hovertext=f"Candidate: {candidate['name']}",name='Candidate'))
 all_lats=[candidate.latitude]+z.lat.tolist();all_lons=[candidate.longitude]+z.lon.tolist();latspan=max(max(all_lats)-min(all_lats),.35);lonspan=max(max(all_lons)-min(all_lons),.55);span=max(latspan,lonspan);zoom=max(3.3,min(7.5,6.5-math.log(span+0.2,2)))
 f.update_geos(scope='europe',projection_type='mercator',center=dict(lat=float(candidate.latitude),lon=float(candidate.longitude)),projection_scale=zoom,showland=True,landcolor='#eef3ef',showocean=True,oceancolor='#e5f0f3',showlakes=True,lakecolor='#dbecef',showcoastlines=True,coastlinecolor='#9eb0a6',showcountries=True,countrycolor='#aebdb5',lataxis_range=[candidate.latitude-span*1.25,candidate.latitude+span*1.25],lonaxis_range=[candidate.longitude-span*1.6,candidate.longitude+span*1.6]);f.update_layout(height=650,margin=dict(l=0,r=0,t=15,b=0),legend=dict(orientation='h'));return f
st.markdown('<div class="hero"><h1>🧭 Location Lifestyle AI V7.2</h1><p>A geographic Journey Map, visible travel trade-offs and a household profile.</p></div>',unsafe_allow_html=True)
with st.sidebar:
 p=st.session_state.profile;st.header('Household profile');preset=st.selectbox('Preset',PRESETS)
 if st.button('Load preset',use_container_width=True):st.session_state.profile=json.loads(json.dumps(PRESETS[preset]));st.rerun()
 p['household']=st.selectbox('Household',['Single','Couple','Family','Retired couple'],index=['Single','Couple','Family','Retired couple'].index(p['household']));p['budget']=st.selectbox('Budget',['Under £500k','£500k–£750k','£750k–£1m','£1m–£2m','£2m+'],index=['Under £500k','£500k–£750k','£750k–£1m','£1m–£2m','£2m+'].index(p['budget']));p['horizon']=st.selectbox('Horizon',['0–3 years','3–8 years','8–15 years'],index=['0–3 years','3–8 years','8–15 years'].index(p['horizon']));p['notes']=st.text_area('What matters',p['notes'],height=85);current=st.selectbox('Current location',L.name,index=int(L.index[L.name=='Marlow'][0]))
 for t in THEMES:p['weights'][t]=st.slider(t,0,10,p['weights'][t],key='w'+t)
 payload={'profile':p,'current':current,'network_floor':st.session_state.floor,'life_network':st.session_state.network.to_dict('records')};st.download_button('Download profile',json.dumps(payload,indent=2),'profile_v72.json','application/json',use_container_width=True)
 upload=st.file_uploader('Import profile',type='json')
 if upload and st.button('Apply imported profile'):
  x=json.load(upload);st.session_state.profile=x['profile'];st.session_state.floor=x.get('network_floor',58);st.session_state.network=pd.DataFrame(x.get('life_network',[]));st.rerun()
out,W=scoring();base=out[out.name==current].iloc[0];focus=sorted(p['weights'],key=p['weights'].get,reverse=True)[:3]
st.markdown(f'<div class="brief"><b>{p["household"]}, {p["budget"]}, {p["horizon"]}:</b> prioritising {focus[0].lower()}, {focus[1].lower()} and {focus[2].lower()}. The Journey Map shows road and public-transport estimates separately.</div>',unsafe_allow_html=True)
tabs=st.tabs(['Journey Map','Life Network editor','Recommendations','Dashboard','Travel table','Compare','Place conversation','Data quality'])
with tabs[0]:
 c1,c2=st.columns([2,1]);candidate_name=c1.selectbox('Candidate location',out.name,index=0);view=c2.radio('Journey view',['Road','Public transport','Both'],horizontal=False);r=out[out.name==candidate_name].iloc[0];z=journeys(r)
 if z.empty:st.info('Add at least one Life Network location in the editor.')
 elif view=='Both':
  a,b=st.columns(2);a.plotly_chart(journey_map(r,z,'Road'),use_container_width=True);b.plotly_chart(journey_map(r,z,'Public transport'),use_container_width=True)
 else:st.plotly_chart(journey_map(r,z,view),use_container_width=True)
 st.caption('Candidate is centred. Nodes use catalogue latitude/longitude. Lines are straight geographic connectors, not road or rail routes. Green ≤60 min, amber 61–120, red >120; thickness indicates importance. Hover shows miles, time and monthly burden.')
with tabs[1]:
 st.subheader('Add, edit and remove important places');edited=st.data_editor(st.session_state.network,num_rows='dynamic',hide_index=True,use_container_width=True,column_config={'Remove':st.column_config.CheckboxColumn('Remove'),'Place':st.column_config.SelectboxColumn(options=L.name.tolist()),'Category':st.column_config.SelectboxColumn(options=['Family','Friends','Home / friends','Travel','Healthcare','Culture','Other']),'Importance':st.column_config.NumberColumn(min_value=1,max_value=10),'Visits/month':st.column_config.NumberColumn(min_value=.1,max_value=30.,step=.5)})
 if st.button('Apply network changes',type='primary'):
  edited=edited[~edited.Remove.fillna(False)].copy();edited['Remove']=False;st.session_state.network=edited;st.rerun()
with tabs[2]:
 floor=st.slider('Minimum Life Network score',0,100,st.session_state.floor);st.session_state.floor=floor;regions=st.multiselect('Regions',sorted(L.region.unique()),default=sorted(L.region.unique()));pool=out[(out.name!=current)&out.region.isin(regions)&(out['Life Network']>=floor)];n=st.slider('Shortlist',5,25,12);x=pool.head(n).copy();x['Road monthly h']=x.apply(lambda r:journeys(r)['Road monthly hours'].sum(),axis=1)
 st.caption(f'{len(pool)} places clear the network gate. Distant counties will not appear unless their Life Network score clears the threshold.');st.dataframe(x[['name','county_area','region','Lifestyle','Life Network','Balanced','Road monthly h']].style.format({'Lifestyle':'{:.1f}','Life Network':'{:.1f}','Balanced':'{:.1f}','Road monthly h':'{:.1f}'}),hide_index=True,use_container_width=True)
with tabs[3]:
 a,b,c,d=st.columns(4);a.metric('Catalogue',len(L));b.metric('Network nodes',len(st.session_state.network));c.metric('Current lifestyle',f"{base.Lifestyle:.0f}");d.metric('Current network',f"{base['Life Network']:.0f}");cs=st.columns(6)
 for i,(t,v) in enumerate(p['weights'].items()):
  with cs[i]:gauge(v*10,t,'g'+t)
with tabs[4]:
 cand=st.selectbox('Candidate',out.name,key='tableplace');r=out[out.name==cand].iloc[0];z=journeys(r);st.dataframe(z[['Place','Category','Importance','Visits/month','Miles','Road minutes','Public transport minutes','Road monthly hours','Public transport monthly hours']].style.format({'Miles':'{:.1f}','Road minutes':'{:.0f}','Public transport minutes':'{:.0f}','Road monthly hours':'{:.1f}','Public transport monthly hours':'{:.1f}'}),hide_index=True,use_container_width=True)
with tabs[5]:
 choices=st.multiselect('Compare 2–4',L.name,default=['Marlow','Winchester','Stamford'],max_selections=4)
 if len(choices)>1:
  c=out[out.name.isin(choices)].set_index('name').copy();c['Road monthly h']=[journeys(r)['Road monthly hours'].sum() for _,r in c.iterrows()];c['Public transport monthly h']=[journeys(r)['Public transport monthly hours'].sum() for _,r in c.iterrows()];st.dataframe(c[['Lifestyle','Life Network','Balanced','Road monthly h','Public transport monthly h','county_area','region']].T,use_container_width=True)
with tabs[6]:
 name=st.selectbox('Discuss',out.name);r=out[out.name==name].iloc[0];drivers=sorted(K,key=lambda k:r[k]*W[k],reverse=True);z=journeys(r);st.subheader(f"{r['name']} · {r['county_area']} · {r['region']}");st.markdown(f"**{LAB[drivers[0]]}**, **{LAB[drivers[1]]}** and **{LAB[drivers[2]]}** are the strongest match drivers. Estimated monthly return burden is **{z['Road monthly hours'].sum():.1f} hours by road proxy** or **{z['Public transport monthly hours'].sum():.1f} hours by public-transport proxy**.\n\n**Profile context:** {p['notes']}")
with tabs[7]:
 st.dataframe(Q,hide_index=True,use_container_width=True);st.dataframe(L[['name','county_area','region','verification_status','coordinate_precision']],hide_index=True,use_container_width=True);st.warning('Journey placement is only as accurate as the catalogue coordinates. Rows marked regional_seed_point require authoritative geocoding. Public-transport estimates do not account for station access, changes, waiting or actual service availability.')
