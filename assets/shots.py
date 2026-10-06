import asyncio
from playwright.async_api import async_playwright

BASE = 'http://localhost:8347'
OUT = '/opt/data/projet/nature-detective/assets'

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 414, 'height': 850},
                              device_scale_factor=2, is_mobile=True, has_touch=True)
        # 1. Home
        await pg.goto(BASE, wait_until='networkidle')
        await pg.screenshot(path=f'{OUT}/shot1_home.png')

        # 2. Result — inject a real past find (bee) into the UI for a clean shot
        await pg.evaluate("""() => {
          const fake = {identified:true, common_name:'Bee', latin_name:'Apis mellifera',
            type:'insect', confidence:'high', safety:'look-dont-touch',
            kid_fact:'Bees talk to each other by dancing! The waggle dance tells the hive exactly where the best flowers are.',
            mission:'Count how many different colored flowers you can spot before the next corner!',
            quiz_question:'True or false: bees talk by dancing.', quiz_answer:true};
          document.getElementById('r-photo').src='/static/demo_bee.jpg';
          document.getElementById('r-name').textContent=fake.common_name;
          document.getElementById('r-latin').textContent=fake.latin_name;
          const b=document.getElementById('r-badge');
          b.className='badge care'; b.textContent="👀 Look, don't touch";
          document.getElementById('r-fact').textContent='💡 '+fake.kid_fact;
          document.getElementById('r-mission').textContent=fake.mission;
          document.getElementById('r-quiz').textContent=fake.quiz_question;
          for(const k in {home:1,load:1,journal:1}) document.getElementById('v-'+k).classList.remove('on');
          document.getElementById('v-result').classList.add('on');
        }""")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=f'{OUT}/shot2_result.png', full_page=True)

        # 3. Journal
        await pg.evaluate("""() => {
          for(const k of ['home','load','result']) document.getElementById('v-'+k).classList.remove('on');
          document.getElementById('v-journal').classList.add('on');
        }""")
        await pg.goto(BASE, wait_until='networkidle')
        await pg.evaluate("""async () => {
          document.getElementById('to-journal').click();
        }""")
        await pg.wait_for_timeout(800)
        await pg.screenshot(path=f'{OUT}/shot3_journal.png')
        await b.close()
        print('screenshots done')

asyncio.run(main())
